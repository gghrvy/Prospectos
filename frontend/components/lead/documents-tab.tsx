"use client";

import { useState } from "react";
import { ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { activityTime } from "@/lib/activity";
import { CONTRACT_TYPE_LABELS, type Contract, type ContractGenerateRequest, type ContractType, type Sender } from "@/lib/types";

export function DocumentsTab({
  contracts,
  demo,
  senders,
  senderId,
  onSenderChange,
  generating,
  onGenerate,
}: {
  contracts: Contract[];
  demo: boolean;
  senders: Sender[];
  senderId: string;
  onSenderChange: (id: string) => void;
  generating: boolean;
  onGenerate: (request: ContractGenerateRequest) => void;
}) {
  const [contractType, setContractType] = useState<ContractType>("SERVICE_AGREEMENT");
  const [studioName, setStudioName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [priceAmount, setPriceAmount] = useState("");
  const [depositPercent, setDepositPercent] = useState(50);
  const sorted = [...contracts].sort((a, b) => b.created_at.localeCompare(a.created_at));

  function submit(event: React.FormEvent) {
    event.preventDefault();
    onGenerate({
      contract_type: contractType,
      sender_id: senderId || undefined,
      studio_name: studioName || undefined,
      project_description: projectDescription || undefined,
      price_amount: priceAmount ? Number(priceAmount) : undefined,
      deposit_percent: depositPercent,
    });
  }

  return (
    <div className={demo ? "max-w-3xl" : "grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]"}>
      <section className="flex min-w-0 flex-col gap-3" aria-label="Documents">
        {sorted.length === 0 ? (
          <EmptyState
            title="No documents yet"
            body={
              demo
                ? "Document templates are turned off in the public demo."
                : "Create a service agreement, NDA or welcome packet for this lead once the work is agreed."
            }
          />
        ) : (
          sorted.map((doc) => (
            <details key={doc.id} className="group rounded-panel border border-rule bg-sheet">
              <summary className="focus-ring flex cursor-pointer list-none items-center gap-3 rounded-panel px-4 py-3 transition-colors duration-fast ease-assay hover:bg-ink/[0.03] [&::-webkit-details-marker]:hidden">
                <ChevronRight size={16} className="shrink-0 text-graphite transition-transform duration-fast ease-assay group-open:rotate-90" aria-hidden="true" />
                <span className="flex-1 text-sm font-medium text-ink">{CONTRACT_TYPE_LABELS[doc.contract_type]}</span>
                <span className="text-[13px] text-graphite">
                  {doc.sender_name ? `${doc.sender_name}, ` : ""}
                  {activityTime(doc.created_at)}
                </span>
              </summary>
              <pre className="whitespace-pre-wrap border-t border-rule/70 px-4 py-4 font-sans text-sm leading-6 text-ink">{doc.content}</pre>
            </details>
          ))
        )}
      </section>

      {!demo && (
        <aside>
          <Card>
            <CardHeader>
              <CardTitle>New document</CardTitle>
              <p className="text-[13px] leading-5 text-graphite">
                A starting template, not legal advice. Have it reviewed before real money changes hands.
              </p>
            </CardHeader>
            <CardContent>
              <form onSubmit={submit} className="flex flex-col gap-4">
                <div>
                  <Label htmlFor="doc-type">Document</Label>
                  <Select id="doc-type" className="w-full" value={contractType} onChange={(e) => setContractType(e.target.value as ContractType)}>
                    {(Object.keys(CONTRACT_TYPE_LABELS) as ContractType[]).map((type) => (
                      <option key={type} value={type}>
                        {CONTRACT_TYPE_LABELS[type]}
                      </option>
                    ))}
                  </Select>
                </div>
                <div>
                  <Label htmlFor="doc-studio">Studio name</Label>
                  <Input id="doc-studio" value={studioName} onChange={(e) => setStudioName(e.target.value)} />
                </div>
                <div>
                  <Label htmlFor="doc-sender">From</Label>
                  <Select id="doc-sender" className="w-full" value={senderId} onChange={(e) => onSenderChange(e.target.value)}>
                    <option value="">No signature</option>
                    {senders.map((sender) => (
                      <option key={sender.id} value={sender.id}>
                        {sender.name}
                      </option>
                    ))}
                  </Select>
                </div>
                {contractType === "SERVICE_AGREEMENT" && (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label htmlFor="doc-fee">Fee (USD)</Label>
                      <Input id="doc-fee" type="number" min={0} inputMode="decimal" value={priceAmount} onChange={(e) => setPriceAmount(e.target.value)} placeholder="2000" />
                    </div>
                    <div>
                      <Label htmlFor="doc-deposit">Deposit %</Label>
                      <Input id="doc-deposit" type="number" min={0} max={100} value={depositPercent} onChange={(e) => setDepositPercent(Number(e.target.value))} />
                    </div>
                  </div>
                )}
                {contractType !== "NDA" && (
                  <div>
                    <Label htmlFor="doc-project">Project</Label>
                    <Textarea
                      id="doc-project"
                      rows={3}
                      value={projectDescription}
                      onChange={(e) => setProjectDescription(e.target.value)}
                      placeholder="A five-page website with online booking"
                    />
                  </div>
                )}
                <Button type="submit" disabled={generating}>
                  {generating ? "Creating…" : `Create ${CONTRACT_TYPE_LABELS[contractType]}`}
                </Button>
              </form>
            </CardContent>
          </Card>
        </aside>
      )}
    </div>
  );
}
