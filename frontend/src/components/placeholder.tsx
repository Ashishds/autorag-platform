import { Construction } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

export function Placeholder({ note }: { note: string }) {
  return (
    <div className="p-8">
      <Card>
        <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
            <Construction className="size-5" />
          </div>
          <p className="text-sm text-muted-foreground">{note}</p>
        </CardContent>
      </Card>
    </div>
  );
}
