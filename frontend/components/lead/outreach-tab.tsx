"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { activityTime } from "@/lib/activity";
import { api, ApiError } from "@/lib/api";
import { OUTREACH_ANGLES, type BusinessDetail, type Outreach, type Sender } from "@/lib/types";

export function OutreachTab({
  business,
  demo,
  gmail,
  senders,
  senderId,
  onSenderChange,
  onSenderCreated,
  angle,
  onAngleChange,
  generating,
  onGenerate,
  busyDraftId,
  onApprove,
  onSend,
}: {
  business: BusinessDetail;
  demo: boolean;
  gmail: { connected: boolean; email: string | null };
  senders: Sender[];
  senderId: string;
  onSenderChange: (id: string) => void;
  onSenderCreated: (sender: Sender) => void;
  angle: string;
  onAngleChange: (angle: string) => void;
  generating: boolean;
  onGenerate: () => void;
  busyDraftId: string | null;
  onApprove: (id: string) => void;
  onSend: (id: string) => void;
}) {
  const [addingSender, setAddingSender] = useState(false);
  const drafts = [...business.outreach_drafts].sort((a, b) => b.created_at.localeCompare(a.created_at));

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
      <section className="flex min-w-0 flex-col gap-4" aria-label="Drafts">
        {drafts.length === 0 ? (
          <EmptyState
            title="No drafts yet"
            body={
              demo
                ? "This sample lead has no prepared draft."
                : "Write a draft from the audit findings. It stays here until someone approves it, and nothing is sent before that."
            }
          />
        ) : (
          drafts.map((draft) => (
            <Draft
              key={draft.id}
              draft={draft}
              recipient={business.email}
              demo={demo}
              gmailConnected={gmail.connected}
              busy={busyDraftId === draft.id}
              onApprove={() => onApprove(draft.id)}
              onSend={() => onSend(draft.id)}
            />
          ))
        )}
      </section>

      <aside className="flex flex-col gap-6">
        {demo ? (
          <Card>
            <CardHeader>
              <CardTitle>How outreach works</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-6 text-graphite">
                In the full version you choose an angle and who it&apos;s from, write a draft from the audit, approve it,
                and send it through Gmail within daily and hourly limits. The public demo shows prepared drafts only.
              </p>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Write a draft</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div>
                <Label htmlFor="outreach-angle">Angle</Label>
                <Select id="outreach-angle" className="w-full" value={angle} onChange={(event) => onAngleChange(event.target.value)}>
                  <option value="">Strongest from the audit</option>
                  {OUTREACH_ANGLES.map((option) => (
                    <option key={option} value={option}>
                      {angleLabel(option)}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <Label htmlFor="outreach-sender">From</Label>
                <Select id="outreach-sender" className="w-full" value={senderId} onChange={(event) => onSenderChange(event.target.value)}>
                  <option value="">No signature</option>
                  {senders.map((sender) => (
                    <option key={sender.id} value={sender.id}>
                      {sender.name}
                    </option>
                  ))}
                </Select>
                <button
                  type="button"
                  onClick={() => setAddingSender((value) => !value)}
                  aria-expanded={addingSender}
                  className="focus-ring mt-1.5 block rounded-[2px] text-[13px] text-survey underline-offset-2 hover:underline"
                >
                  {addingSender ? "Cancel adding a teammate" : "Add a teammate"}
                </button>
              </div>
              {addingSender && (
                <AddSenderForm
                  onCreated={(sender) => {
                    setAddingSender(false);
                    onSenderCreated(sender);
                  }}
                />
              )}
              <Button variant="outline" onClick={onGenerate} disabled={generating}>
                {generating ? "Writing draft…" : "Write draft"}
              </Button>
            </CardContent>
          </Card>
        )}

        <Card className="p-4 text-sm">
          <p className="text-graphite">Gmail</p>
          <p className="mt-0.5 text-ink">{gmail.connected ? `Connected as ${gmail.email}` : "Not connected"}</p>
          {!demo && !gmail.connected && (
            <Button
              size="sm"
              variant="outline"
              className="mt-3"
              onClick={() => {
                window.location.href = api.gmailConnectUrl();
              }}
            >
              Connect Gmail
            </Button>
          )}
        </Card>
      </aside>
    </div>
  );
}

const GENERATORS: Record<string, string> = {
  ollama: "with Ollama",
  template: "from a template",
  "prepared-demo": "as sample data",
};

function generatorLabel(name: string): string {
  return GENERATORS[name] ?? `by ${name}`;
}

function angleLabel(angle: string): string {
  const text = angle.replace(/_/g, " ").toLowerCase();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// A draft reads like the email it will become: headers, subject, body. Its
// footer says exactly where it is in approve-then-send.
function Draft({
  draft,
  recipient,
  demo,
  gmailConnected,
  busy,
  onApprove,
  onSend,
}: {
  draft: Outreach;
  recipient: string | null;
  demo: boolean;
  gmailConnected: boolean;
  busy: boolean;
  onApprove: () => void;
  onSend: () => void;
}) {
  const approved = draft.approval_status === "APPROVED";
  return (
    <Card role="article" aria-label={draft.subject ?? "Draft"}>
      <div className="grid grid-cols-[56px_minmax(0,1fr)] gap-x-3 gap-y-1 border-b border-rule/70 px-4 py-3 text-[13px]">
        <span className="text-graphite">To</span>
        <span className="text-ink">{draft.sent_to ?? recipient ?? "No email address found"}</span>
        <span className="text-graphite">From</span>
        <span className="text-ink">{draft.sender_name ?? "No signature"}</span>
        {draft.angle && (
          <>
            <span className="text-graphite">Angle</span>
            <span className="text-ink">{angleLabel(draft.angle)}</span>
          </>
        )}
      </div>
      <div className="px-4 py-4">
        <h3 className="text-base font-semibold text-ink">{draft.subject ?? "No subject"}</h3>
        <p className="mt-3 max-w-prose whitespace-pre-wrap text-sm leading-6 text-ink">{draft.body}</p>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-rule/70 px-4 py-3 text-[13px]">
        <span className="text-graphite">
          Written {activityTime(draft.created_at)}
          {draft.generated_by ? ` ${generatorLabel(draft.generated_by)}` : ""}
        </span>
        {draft.sent_at ? (
          <span className="font-medium text-survey">Sent {activityTime(draft.sent_at)}</span>
        ) : demo ? (
          <span className="text-graphite">Preview only. Nothing is sent from the demo.</span>
        ) : !approved ? (
          <Button size="sm" variant="outline" disabled={busy} onClick={onApprove}>
            {busy ? "Approving…" : "Approve for sending"}
          </Button>
        ) : (
          <span className="flex items-center gap-3">
            {!recipient && <span className="text-graphite">No email address to send to</span>}
            {recipient && !gmailConnected && <span className="text-graphite">Connect Gmail to send</span>}
            <Button size="sm" disabled={!gmailConnected || !recipient || busy} onClick={onSend}>
              {busy ? "Sending…" : "Send with Gmail"}
            </Button>
          </span>
        )}
      </div>
    </Card>
  );
}

function AddSenderForm({ onCreated }: { onCreated: (sender: Sender) => void }) {
  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [email, setEmail] = useState("");
  const [portfolioUrl, setPortfolioUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) {
      setError("Add a name so drafts can be signed.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const sender = await api.createSender({
        name,
        title: title || null,
        email: email || null,
        portfolio_url: portfolioUrl || null,
      });
      onCreated(sender);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The teammate couldn't be saved. Try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-3 rounded-control border border-rule bg-paper p-3">
      <div>
        <Label htmlFor="sender-name">
          Name <span className="text-brick" aria-hidden="true">*</span>
        </Label>
        <Input id="sender-name" value={name} onChange={(e) => setName(e.target.value)} required aria-invalid={Boolean(error)} />
      </div>
      <div>
        <Label htmlFor="sender-title">Title</Label>
        <Input id="sender-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Web developer" />
      </div>
      <div>
        <Label htmlFor="sender-email">Email</Label>
        <Input id="sender-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      </div>
      <div>
        <Label htmlFor="sender-link">Portfolio or contact link</Label>
        <Input id="sender-link" type="url" value={portfolioUrl} onChange={(e) => setPortfolioUrl(e.target.value)} placeholder="https://" />
      </div>
      {error && (
        <p role="alert" className="text-[13px] text-brick">
          {error}
        </p>
      )}
      <Button type="submit" size="sm" variant="outline" disabled={saving} className="self-start">
        {saving ? "Saving…" : "Save teammate"}
      </Button>
    </form>
  );
}
