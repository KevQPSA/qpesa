import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

interface DocumentationTableProps {
  data?: {
    property: string
    type: string
    description: string
  }[]
}

export function DocumentationTable({ data = [] }: DocumentationTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-semibold">API Documentation</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Property</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Description</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center py-4 text-muted-foreground">
                  No data available.
                </TableCell>
              </TableRow>
            ) : (
              data.map((row, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{row.property}</TableCell>
                  <TableCell>{row.type}</TableCell>
                  <TableCell>{row.description}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
