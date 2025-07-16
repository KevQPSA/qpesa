import { SiteHeader } from "@/components/site-header"
import { SiteFooter } from "@/components/site-footer"
import { DocumentationTable } from "@/components/documentation-table"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function HomePage() {
  // Sample data for the DocumentationTable
  const apiDocumentationData = [
    { property: "endpoint", type: "string", description: "API endpoint path" },
    { property: "method", type: "string", description: "HTTP method (GET, POST, PUT, DELETE)" },
    { property: "description", type: "string", description: "Brief description of the endpoint" },
    { property: "auth_required", type: "boolean", description: "Indicates if authentication is required" },
    { property: "response_schema", type: "object", description: "JSON schema of the expected response" },
  ]

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1 container py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight lg:text-4xl">
            Up-to-date documentation for LLMs and AI code editors
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            Copy the latest docs and code for any library — paste into Cursor, Claude, or other LLMs.
          </p>
        </div>
        <DocumentationTable data={apiDocumentationData} />
        <div className="mt-8">
          <Button variant="outline" asChild>
            <Link href="#">Return to homepage</Link>
          </Button>
        </div>
      </main>
      <SiteFooter />
    </div>
  )
}
