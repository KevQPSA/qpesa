"""
Bitcoin blockchain integration service
Handles Bitcoin transactions, address generation, and monitoring
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from datetime import datetime, timezone
import hashlib
import hmac
import json

import httpx
from bitcoinlib.wallets import Wallet as BitcoinWallet
from bitcoinlib.keys import HDKey
from bitcoinlib.transactions import Transaction
from bitcoinlib.encoding import to_hexstring

from app.core.config import settings
from app.core.exceptions import BlockchainError, ValidationError
from app.domain.value_objects import Money, WalletAddress, TransactionHash, Currency, EncryptedPrivateKey
from app.domain.entities import CryptoWallet, TransactionRecord, PaymentStatus
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class BitcoinService:
    """
    Bitcoin blockchain service for transaction processing
    Implements secure Bitcoin operations with proper error handling
    """
    
    def __init__(self):
        self.rpc_url = settings.BITCOIN_RPC_URL
        self.rpc_user = settings.BITCOIN_RPC_USER
        self.rpc_password = settings.BITCOIN_RPC_PASSWORD
        self.network = settings.BITCOIN_NETWORK
        self.min_confirmations = settings.BTC_CONFIRMATIONS_REQUIRED
        self.client = httpx.AsyncClient(timeout=30.0, limits=httpx.Limits(max_connections=10, max_keepalive_connections=5))
        logger.info("BitcoinService initialized (simulated)")

    @asynccontextmanager
    async def __aenter__(self):
        """Async context manager entry point"""
        # Simulate async setup if needed
        yield self
        # Simulate async cleanup if needed
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _rpc_call(self, method: str, params: List[Any] = None) -> Dict[str, Any]:
        """
        Make RPC call to Bitcoin node
        Implements proper authentication and error handling
        """
        if params is None:
            params = []
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        auth = httpx.BasicAuth(self.rpc_user, self.rpc_password)
        
        try:
            response = await self.client.post(
                self.rpc_url,
                json=payload,
                auth=auth,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result and result["error"]:
                raise BlockchainError(
                    f"Bitcoin RPC error: {result['error']['message']}",
                    details={"method": method, "params": params}
                )
            
            return result.get("result")
            
        except httpx.RequestError as e:
            logger.error(f"Bitcoin RPC request failed: {str(e)}")
            raise BlockchainError(f"Bitcoin node connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Bitcoin RPC call failed: {str(e)}")
            raise BlockchainError(f"Bitcoin RPC call failed: {str(e)}")
    
    async def generate_wallet_address(self, user_id: str, derivation_index: int = 0) -> CryptoWallet:
        """
        Generate new Bitcoin wallet address using HD wallet
        Implements BIP44 derivation path for security
        """
        try:
            # Create HD wallet for user
            # In production, use a master seed stored securely
            master_key = HDKey.from_seed(f"qpesapay-{user_id}".encode())
            
            # BIP44 derivation path: m/44'/0'/0'/0/index
            derivation_path = f"m/44'/0'/0'/0/{derivation_index}"
            derived_key = master_key.subkey_for_path(derivation_path)
            
            # Generate address
            address = derived_key.address()
            
            # Create wallet address value object
            wallet_address = WalletAddress(address=address, network=Network.BITCOIN)
            
            # Create encrypted private key
            encrypted_key = EncryptedPrivateKey.encrypt(
                derived_key.wif(),
                settings.ENCRYPTION_KEY.encode()
            )
            
            # Create wallet entity
            wallet = CryptoWallet(
                user_id=user_id,
                currency=Currency.BTC,
                address=wallet_address,
                encrypted_private_key=encrypted_key,
                balance=Money(Decimal('0'), Currency.BTC)
            )
            
            logger.info(f"Generated Bitcoin wallet for user {user_id}: {address}")
            return wallet
            
        except Exception as e:
            logger.error(f"Failed to generate Bitcoin wallet: {str(e)}")
            raise BlockchainError(f"Failed to generate Bitcoin wallet: {str(e)}")
    
    async def get_address_balance(self, address: WalletAddress) -> Money:
        """
        Get Bitcoin balance for address
        Uses Bitcoin Core RPC for accurate balance
        """
        if address.network != Network.BITCOIN:
            raise ValidationError("Address must be Bitcoin network")
        
        try:
            # Get unspent transaction outputs
            utxos = await self._rpc_call("listunspent", [0, 9999999, [address.address]])
            
            total_satoshis = sum(int(utxo["amount"] * 100000000) for utxo in utxos)
            balance_btc = Decimal(total_satoshis) / Decimal('100000000')
            
            return Money(balance_btc, Currency.BTC)
            
        except Exception as e:
            logger.error(f"Failed to get Bitcoin balance for {address.address}: {str(e)}")
            raise BlockchainError(f"Balance check failed: {str(e)}")
    
    async def estimate_transaction_fee(self, 
                                     from_address: str,
                                     to_address: str, 
                                     amount: Money) -> Money:
        """
        Estimate Bitcoin transaction fee
        """
        try:
            # Get current fee rate (satoshis per byte)
            fee_rate_result = await self._rpc_call("estimatesmartfee", [6])  # 6 blocks target
            
            if 'feerate' not in fee_rate_result:
                # Fallback to default fee rate
                fee_rate_btc_per_kb = Decimal('0.00001')  # 1000 sats/KB
            else:
                fee_rate_btc_per_kb = Decimal(str(fee_rate_result['feerate']))
            
            # Estimate transaction size (simplified)
            # Typical transaction: 1 input + 2 outputs ≈ 250 bytes
            estimated_size_bytes = 250
            estimated_size_kb = Decimal(estimated_size_bytes) / Decimal('1000')
            
            estimated_fee = fee_rate_btc_per_kb * estimated_size_kb
            
            # Add 10% buffer for fee estimation uncertainty
            estimated_fee *= Decimal('1.1')
            
            return Money(estimated_fee, Currency.BTC)
            
        except Exception as e:
            logger.error(f"Failed to estimate Bitcoin fee: {str(e)}")
            # Return conservative fallback fee
            return Money(Decimal('0.0001'), Currency.BTC)
    
    async def send_transaction(self,
                             from_wallet: CryptoWallet,
                             to_address: str,
                             amount: Money,
                             fee: Money) -> TransactionRecord:
        """
        Send Bitcoin transaction with proper validation and error handling
        """
        try:
            # Validate inputs
            if amount.currency != Currency.BTC or fee.currency != Currency.BTC:
                raise ValidationError("Amount and fee must be in BTC")
            
            if not from_wallet.can_send(amount.add(fee)):
                raise ValidationError("Insufficient balance for transaction")
            
            # Decrypt private key
            private_key_wif = from_wallet.encrypted_private_key.decrypt(
                settings.ENCRYPTION_KEY.encode()
            )
            
            # Create transaction (simplified - in production use proper UTXO management)
            to_address_obj = WalletAddress(to_address, 'bitcoin')
            
            # Get UTXOs for the from address
            utxos = await self._rpc_call("listunspent", [0, 9999999, [from_wallet.address.address]])
            
            if not utxos:
                raise ValidationError("No unspent outputs available")
            
            # Select UTXOs (simplified - use first available)
            selected_utxos = []
            total_input = Decimal('0')
            required_amount = amount.amount + fee.amount
            
            for utxo in utxos:
                selected_utxos.append(utxo)
                total_input += Decimal(str(utxo['amount']))
                if total_input >= required_amount:
                    break
            
            if total_input < required_amount:
                raise ValidationError("Insufficient UTXOs for transaction")
            
            # Create raw transaction
            inputs = []
            for utxo in selected_utxos:
                inputs.append({
                    "txid": utxo['txid'],
                    "vout": utxo['vout']
                })
            
            outputs = {
                to_address: float(amount.amount)
            }
            
            # Add change output if necessary
            change_amount = total_input - required_amount
            if change_amount > Decimal('0.00001'):  # Dust threshold
                outputs[from_wallet.address.address] = float(change_amount)
            
            # Create and sign transaction
            raw_tx = await self._rpc_call("createrawtransaction", [inputs, outputs])
            signed_tx = await self._rpc_call("signrawtransactionwithkey", [raw_tx, [private_key_wif]])
            
            if not signed_tx.get('complete'):
                raise BlockchainError("Failed to sign transaction")
            
            # Broadcast transaction
            tx_hash = await self._rpc_call("sendrawtransaction", [signed_tx['hex']])
            
            # Create transaction record
            transaction_hash = TransactionHash(tx_hash, 'bitcoin')
            
            transaction_record = TransactionRecord(
                user_id=from_wallet.user_id,
                amount=amount,
                fee=fee,
                from_address=from_wallet.address,
                to_address=to_address_obj,
                transaction_hash=transaction_hash,
                status=PaymentStatus.PENDING
            )
            
            transaction_record.calculate_net_amount()
            transaction_record.add_audit_entry("transaction_broadcast", {
                "tx_hash": tx_hash,
                "amount": str(amount.amount),
                "fee": str(fee.amount),
                "to_address": to_address
            })
            
            logger.info(f"Bitcoin transaction sent: {tx_hash}")
            return transaction_record
            
        except Exception as e:
            logger.error(f"Failed to send Bitcoin transaction: {str(e)}")
            raise BlockchainError(f"Failed to send Bitcoin transaction: {str(e)}")
    
    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get Bitcoin transaction status and confirmation count
        """
        try:
            # Get transaction details
            tx_info = await self._rpc_call("gettransaction", [tx_hash])
            
            confirmations = tx_info.get('confirmations', 0)
            block_hash = tx_info.get('blockhash')
            block_number = None
            
            if block_hash:
                block_info = await self._rpc_call("getblock", [block_hash])
                block_number = block_info.get('height')
            
            return {
                'confirmations': confirmations,
                'block_number': block_number,
                'block_hash': block_hash,
                'status': 'confirmed' if confirmations >= self.min_confirmations else 'pending'
            }
            
        except Exception as e:
            logger.error(f"Failed to get Bitcoin transaction status: {str(e)}")
            raise BlockchainError(f"Failed to get transaction status: {str(e)}")
    
    async def monitor_address(self, address: str, callback_url: Optional[str] = None) -> None:
        """
        Monitor Bitcoin address for incoming transactions
        Implements efficient monitoring with minimal resource usage
        """
        try:
            logger.info(f"Starting Bitcoin address monitoring for: {address}")
            
            # In production, this would use webhooks or a more efficient monitoring system
            # For now, implement basic polling
            last_balance = await self.get_address_balance(address)
            
            while True:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                try:
                    current_balance = await self.get_address_balance(address)
                    
                    if current_balance.amount != last_balance.amount:
                        logger.info(f"Balance change detected for {address}: {current_balance}")
                        
                        # In production, trigger webhook or event
                        if callback_url:
                            await self._notify_balance_change(callback_url, address, current_balance)
                        
                        last_balance = current_balance
                        
                except Exception as e:
                    logger.error(f"Error monitoring address {address}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to start monitoring for {address}: {str(e)}")
    
    async def _notify_balance_change(self, callback_url: str, address: str, balance: Money):
        """
        Notify about balance changes via webhook
        """
        try:
            payload = {
                'address': address,
                'balance': str(balance.amount),
                'currency': balance.currency.code,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(callback_url, json=payload)
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f"Failed to notify balance change: {str(e)}")
    
    async def validate_address(self, address: str) -> bool:
        """
        Validate Bitcoin address format and checksum
        Uses Bitcoin Core validation for accuracy
        """
        try:
            result = await self._rpc_call("validateaddress", [address])
            return result.get('isvalid', False)
            
        except Exception as e:
            logger.error(f"Failed to validate Bitcoin address: {str(e)}")
            return False
    
    async def get_network_info(self) -> Dict[str, Any]:
        """
        Get Bitcoin network information for monitoring
        """
        try:
            network_info = await self._rpc_call("getnetworkinfo")
            blockchain_info = await self._rpc_call("getblockchaininfo")
            
            return {
                'network': self.network,
                'connections': network_info.get('connections'),
                'blocks': blockchain_info.get('blocks'),
                'difficulty': blockchain_info.get('difficulty'),
                'chain': blockchain_info.get('chain')
            }
            
        except Exception as e:
            logger.error(f"Failed to get Bitcoin network info: {str(e)}")
            raise BlockchainError(f"Failed to get network info: {str(e)}")
    
    async def get_transaction_info(self, tx_hash: TransactionHash) -> Dict[str, Any]:
        """
        Simulates fetching Bitcoin transaction information.
        In a real system, this would query a blockchain explorer or node.
        """
        try:
            # Simulate transaction confirmations and status
            # For a real system, you'd query the blockchain for actual confirmations
            mock_confirmations = 3 # Assume it's confirmed for testing purposes
            mock_status = "confirmed" if mock_confirmations >= 3 else "pending"
            
            logger.info(f"Simulated Bitcoin transaction info for {tx_hash.hash}: Status={mock_status}, Confirmations={mock_confirmations}")
            
            return {
                "hash": tx_hash.hash,
                "status": mock_status,
                "confirmations": mock_confirmations,
                "amount": 0.001, # Example amount
                "network": Network.BITCOIN.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get Bitcoin transaction info for {tx_hash.hash}: {e}")
            raise BlockchainError("Failed to retrieve Bitcoin transaction info")

    async def broadcast_transaction(self, signed_tx_hex: str) -> TransactionHash:
        """
        Simulates broadcasting a signed Bitcoin transaction.
        """
        await asyncio.sleep(0.5) # Simulate network latency
        mock_tx_hash = TransactionHash(hash=f"mock_btc_tx_{hash(signed_tx_hex)}", network=Network.BITCOIN)
        logger.info(f"Simulated Bitcoin transaction broadcast: {mock_tx_hash.hash}")
        return mock_tx_hash

# Utility functions for Bitcoin operations
def generate_bitcoin_private_key() -> str:
    """Generate secure Bitcoin private key"""
    key = HDKey.generate()
    return key.wif()

def bitcoin_address_to_script_hash(address: str) -> str:
    """Convert Bitcoin address to script hash for Electrum servers"""
    # This would be used for Electrum server integration
    # Implementation depends on address type (P2PKH, P2SH, Bech32)
    pass

def calculate_bitcoin_fee(tx_size_bytes: int, fee_rate_sat_per_byte: int) -> Money:
    """Calculate Bitcoin transaction fee"""
    fee_satoshis = tx_size_bytes * fee_rate_sat_per_byte
    fee_btc = Decimal(fee_satoshis) / Decimal('100000000')
    return Money(fee_btc, Currency.BTC)
