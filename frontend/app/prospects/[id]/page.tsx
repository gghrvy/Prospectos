"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { OpportunityScoreBadge, QualityBadge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, PrimaryCard } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api, ApiError } from "@/lib/api";
import { Input } from "@/components/ui/input";
import {
  CONTRACT_TYPE_LABELS,
  LEAD_STATUSES,
  LEAD_STATUS_LABELS,
  OPPORTUNITY_TYPE_LABELS,
  OUTREACH_ANGLES,
  type BusinessDetail,
  type ContractType,
  type Sender,
} from "@/lib/types";

export default function ProspectDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const businessId = params.id;

  const [business, setBusiness] = useState<BusinessDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [auditing, setAuditing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [angle, setAngle] = useState("");

  const [senders, setSenders] = useState<Sender[]>([]);
  const [senderId, setSenderId] = useState("");
  const [showAddSender, setShowAddSender] = useState(false);

  const [contractType, setContractType] = useState<ContractType>("SERVICE_AGREEMENT");
  const [studioName, setStudioName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [priceAmount, setPriceAmount] = useState("");
  const [depositPercent, setDepositPercent] = useState(50);
  const [generatingContract, setGeneratingContract] = useState(false);

  const load = useCallback(() => {
    api
      .getBusiness(businessId)
      .then(setBusiness)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load prospect."));
  }, [businessId]);

  const loadSenders = useCallback(() => {
    api
      .listSenders()
      .then((list) => {
        setSenders(list);
        // Remember the last-used sender across visits (per browser) so you
        // don't have to reselect a teammate on every single business.
        const remembered = localStorage.getItem("prospectos_sender_id");
        if (remembered && list.some((s) => s.id === remembered)) {
          setSenderId(remembered);
        } else if (list.length > 0 && !senderId) {
          setSenderId(list[0].id);
        }
      })
      .catch(() => {
        // Non-fatal -- outreach can still be generated without a sender,
        // it just won't have a real signature.
      });
  }, [senderId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    loadSenders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (senderId) localStorage.setItem("prospectos_sender_id", senderId);
  }, [senderId]);

  async function handleRunAudit() {
    setAuditing(true);
    setError(null);
    try {
      await api.runAudit(businessId);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Audit failed.");
    } finally {
      setAuditing(false);
    }
  }

  async function handleGenerateOutreach() {
    setGenerating(true);
    setError(null);
    try {
      await api.generateOutreach(businessId, { angle: angle || undefined, sender_id: senderId || undefined });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Outreach generation failed.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleGenerateContract() {
    setGeneratingContract(true);
    setError(null);
    try {
      await api.generateContract(businessId, {
        contract_type: contractType,
        sender_id: senderId || undefined,
        studio_name: studioName || undefined,
        project_description: projectDescription || undefined,
        price_amount: priceAmount ? Number(priceAmount) : undefined,
        deposit_percent: depositPercent,
      });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Contract generation failed.");
    } finally {
      setGeneratingContract(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Delete this prospect and all of its audit/outreach/note history? This cannot be undone.")) return;
    try {
      await api.deleteBusiness(businessId);
      router.push("/prospects");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed.");
    }
  }

  if (error && !business) {
    return (
      <div className="flex flex-col gap-4">
        <Link href="/prospects" className="text-sm text-muted-foreground hover:underline">
          ← Back to prospects
        </Link>
        <p className="text-sm text-red-400">{error}</p>
      </div>
    );
  }

  if (!business) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  const audit = business.latest_audit;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link href="/prospects" className="text-sm text-muted-foreground hover:underline">
          ← Back to prospects
        </Link>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{business.name}</h1>
            <StatusBadge status={business.current_status} />
          </div>
          <p className="text-sm text-muted-foreground">
            {[business.category, business.city, business.state, business.country].filter(Boolean).join(" · ") || "—"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleRunAudit} disabled={auditing}>
            {auditing ? "Auditing…" : business.audits.length ? "Re-run audit" : "Run audit"}
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            Delete
          </Button>
        </div>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Contact info</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-1 text-sm">
            <InfoRow label="Website">
              {business.website ? (
                <a href={business.website} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                  {business.website}
                </a>
              ) : (
                <span className="text-muted-foreground">Website not found from available sources.</span>
              )}
            </InfoRow>
            {!business.website && business.social_url && (
              <InfoRow label="Social">
                <a href={business.social_url} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                  {business.social_url.includes("instagram.com") ? "Instagram page" : "Facebook page"}
                </a>
                <span className="ml-2 text-xs text-muted-foreground">(no automated send — DM manually)</span>
              </InfoRow>
            )}
            <InfoRow label="Phone">{business.phone ?? "—"}</InfoRow>
            <InfoRow label="Email">{business.email ?? "—"}</InfoRow>
            <InfoRow label="Address">{business.address ?? "—"}</InfoRow>
            <InfoRow label="Source">{business.source ?? "—"}</InfoRow>
            <InfoRow label="Rating">
              {business.rating !== null ? `${business.rating} (${business.review_count ?? 0} reviews)` : "—"}
            </InfoRow>
            {business.google_maps_url && (
              <InfoRow label="Maps">
                <a href={business.google_maps_url} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                  Open in Maps
                </a>
              </InfoRow>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Lead status</CardTitle>
          </CardHeader>
          <CardContent>
            <StatusChangeForm businessId={businessId} onChanged={load} />
            <div className="mt-4 flex flex-col gap-2">
              {business.status_history.length === 0 ? (
                <p className="text-xs text-muted-foreground">No status changes yet.</p>
              ) : (
                business.status_history.map((h) => (
                  <div key={h.id} className="border-t border-border pt-2 text-xs">
                    <div className="flex items-center gap-2">
                      <StatusBadge status={h.status} />
                      <span className="text-muted-foreground">{new Date(h.created_at).toLocaleString()}</span>
                    </div>
                    {h.note && <p className="mt-1 text-muted-foreground">{h.note}</p>}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Scores</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2 text-sm">
            {audit ? (
              <>
                <InfoRow label="Quality">
                  <QualityBadge category={audit.quality_category} />
                </InfoRow>
                <InfoRow label="Overall opportunity">
                  <OpportunityScoreBadge score={audit.overall_opportunity_score} />
                </InfoRow>
                <InfoRow label="AI opportunity">
                  <OpportunityScoreBadge score={audit.ai_opportunity_score} />
                </InfoRow>
                <InfoRow label="Redesign opportunity">
                  <OpportunityScoreBadge score={audit.redesign_opportunity_score} />
                </InfoRow>
                <InfoRow label="Website quality">
                  <OpportunityScoreBadge score={audit.website_quality_score} />
                </InfoRow>
              </>
            ) : (
              <p className="text-xs text-muted-foreground">No audit run yet — click &quot;Run audit&quot; above.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {audit && (
        <PrimaryCard>
          <CardHeader>
            <CardTitle>Latest audit — {new Date(audit.created_at).toLocaleString()}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-sm">{audit.audit_summary}</p>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-6">
              <SubScore label="Mobile" score={audit.mobile_score} />
              <SubScore label="Design" score={audit.design_score} />
              <SubScore label="Technical" score={audit.technical_score} />
              <SubScore label="Content" score={audit.content_score} />
              <SubScore label="Conversion" score={audit.conversion_score} />
              <SubScore label="Cust. experience" score={audit.customer_experience_score} />
            </div>

            <div>
              <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                Opportunity areas
              </p>
              <div className="flex flex-wrap gap-1.5">
                {(audit.opportunity_types ?? []).map((t) => (
                  <span
                    key={t}
                    className="rounded-sm border border-signal/30 bg-signal/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-signal"
                  >
                    {OPPORTUNITY_TYPE_LABELS[t] ?? t}
                  </span>
                ))}
              </div>
            </div>

            {audit.opportunity_reasons && audit.opportunity_reasons.length > 0 && (
              <div>
                <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Why</p>
                <ul className="list-inside list-disc text-sm text-muted-foreground">
                  {audit.opportunity_reasons.map((reason, i) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
              {audit.url && <span>Crawled {audit.page_count ?? 0} page(s), depth {audit.crawl_depth ?? 0}</span>}
              {audit.https_enabled !== null && <span>· HTTPS: {audit.https_enabled ? "yes" : "no"}</span>}
              {audit.broken_link_count !== null && <span>· {audit.broken_link_count} broken link(s)</span>}
            </div>

            {(audit.screenshot_desktop_path || audit.screenshot_mobile_path) && (
              <div className="flex flex-wrap gap-4">
                {audit.screenshot_desktop_path && (
                  <Screenshot label="Desktop" path={audit.screenshot_desktop_path} />
                )}
                {audit.screenshot_mobile_path && <Screenshot label="Mobile" path={audit.screenshot_mobile_path} />}
              </div>
            )}
          </CardContent>
        </PrimaryCard>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Outreach</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <Label>Angle (optional)</Label>
              <Select value={angle} onChange={(e) => setAngle(e.target.value)}>
                <option value="">Auto-pick strongest angle</option>
                {OUTREACH_ANGLES.map((a) => (
                  <option key={a} value={a}>
                    {a.replace(/_/g, " ")}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Sending as</Label>
              <Select value={senderId} onChange={(e) => setSenderId(e.target.value)}>
                <option value="">No signature (name/contact left blank)</option>
                {senders.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
            </div>
            <Button variant="outline" type="button" onClick={() => setShowAddSender((v) => !v)}>
              {showAddSender ? "Cancel" : "+ Add teammate"}
            </Button>
            <Button onClick={handleGenerateOutreach} disabled={generating}>
              {generating ? "Generating…" : "Generate outreach draft"}
            </Button>
          </div>

          {showAddSender && (
            <AddSenderForm
              onCreated={(sender) => {
                setShowAddSender(false);
                loadSenders();
                setSenderId(sender.id);
              }}
            />
          )}

          {business.outreach_drafts.length === 0 ? (
            <p className="text-sm text-muted-foreground">No drafts yet.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {business.outreach_drafts.map((draft) => (
                <div key={draft.id} className="rounded-md border border-border p-3">
                  <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
                    <span>
                      {draft.angle?.replace(/_/g, " ") ?? "—"} · via {draft.generated_by ?? "unknown"}
                      {draft.sender_name ? ` · sent by ${draft.sender_name}` : ""}
                    </span>
                    <span>{new Date(draft.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-sm font-medium">{draft.subject}</p>
                  <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">{draft.body}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Contracts &amp; documents</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-xs text-muted-foreground">
            Starting-point templates, not legal advice — review with a real lawyer (or the commercial-legal
            plugin) before sending for real money.
          </p>
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <Label>Document type</Label>
              <Select value={contractType} onChange={(e) => setContractType(e.target.value as ContractType)}>
                {(Object.keys(CONTRACT_TYPE_LABELS) as ContractType[]).map((t) => (
                  <option key={t} value={t}>
                    {CONTRACT_TYPE_LABELS[t]}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Studio name</Label>
              <Input value={studioName} onChange={(e) => setStudioName(e.target.value)} placeholder="e.g. Acme Studio" />
            </div>
            <div>
              <Label>Sending as</Label>
              <Select value={senderId} onChange={(e) => setSenderId(e.target.value)}>
                <option value="">No signature</option>
                {senders.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          {contractType === "SERVICE_AGREEMENT" && (
            <div className="flex flex-wrap items-end gap-3">
              <div>
                <Label>Project fee (USD)</Label>
                <Input
                  type="number"
                  value={priceAmount}
                  onChange={(e) => setPriceAmount(e.target.value)}
                  placeholder="2000"
                  className="w-32"
                />
              </div>
              <div>
                <Label>Deposit %</Label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={depositPercent}
                  onChange={(e) => setDepositPercent(Number(e.target.value))}
                  className="w-24"
                />
              </div>
            </div>
          )}
          {contractType !== "NDA" && (
            <div>
              <Label>Project description</Label>
              <Textarea
                value={projectDescription}
                onChange={(e) => setProjectDescription(e.target.value)}
                placeholder="e.g. a 5-page marketing website with an integrated AI chatbot"
                rows={2}
              />
            </div>
          )}
          <Button onClick={handleGenerateContract} disabled={generatingContract} className="self-start">
            {generatingContract ? "Generating…" : `Generate ${CONTRACT_TYPE_LABELS[contractType]}`}
          </Button>

          {business.contracts.length === 0 ? (
            <p className="text-sm text-muted-foreground">No documents yet.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {business.contracts.map((doc) => (
                <details key={doc.id} className="rounded-md border border-border p-3">
                  <summary className="cursor-pointer text-sm font-medium">
                    {CONTRACT_TYPE_LABELS[doc.contract_type]}
                    {doc.sender_name ? ` · by ${doc.sender_name}` : ""}
                    <span className="ml-2 font-mono text-xs text-muted-foreground">
                      {new Date(doc.created_at).toLocaleString()}
                    </span>
                  </summary>
                  <pre className="mt-2 whitespace-pre-wrap font-sans text-sm text-muted-foreground">{doc.content}</pre>
                </details>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <NotesSection businessId={businessId} notes={business.notes} onAdded={load} />
        </CardContent>
      </Card>
    </div>
  );
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right">{children}</span>
    </div>
  );
}

function SubScore({ label, score }: { label: string; score: number | null }) {
  const color = score === null ? "" : score >= 70 ? "bg-emerald-400" : score >= 40 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="rounded-sm border border-border bg-panel-raised p-2 text-center">
      <div className="font-mono text-lg font-semibold tabular-nums">{score ?? "—"}</div>
      {score !== null && (
        <div className="mx-auto mt-1 h-1 w-10 overflow-hidden rounded-full bg-border">
          <div className={`h-full ${color}`} style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
        </div>
      )}
      <div className="mt-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
    </div>
  );
}

function Screenshot({ label, path }: { label: string; path: string }) {
  const url = api.screenshotUrl(path);
  if (!url) return null;
  return (
    <div>
      <p className="mb-1 text-xs text-muted-foreground">{label}</p>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={url} alt={`${label} screenshot`} className="max-h-64 rounded-md border border-border" />
    </div>
  );
}

function StatusChangeForm({ businessId, onChanged }: { businessId: string; onChanged: () => void }) {
  const [status, setStatus] = useState("");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!status) {
      setError("Choose a status.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.changeStatus(businessId, { status: status as never, note: note || undefined });
      setNote("");
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update status.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-2">
      <Select value={status} onChange={(e) => setStatus(e.target.value)}>
        <option value="">Change status to…</option>
        {LEAD_STATUSES.map((s) => (
          <option key={s} value={s}>
            {LEAD_STATUS_LABELS[s]}
          </option>
        ))}
      </Select>
      <Textarea placeholder="Note (optional)" value={note} onChange={(e) => setNote(e.target.value)} rows={2} />
      <Button type="submit" size="sm" disabled={saving}>
        {saving ? "Saving…" : "Update status"}
      </Button>
      {error && <span className="text-xs text-red-400">{error}</span>}
    </form>
  );
}

function NotesSection({
  businessId,
  notes,
  onAdded,
}: {
  businessId: string;
  notes: BusinessDetail["notes"];
  onAdded: () => void;
}) {
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    setSaving(true);
    try {
      await api.addNote(businessId, { content });
      setContent("");
      onAdded();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={submit} className="flex flex-col gap-2">
        <Textarea
          placeholder="Add a note…"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={2}
        />
        <Button type="submit" size="sm" disabled={saving} className="self-start">
          {saving ? "Adding…" : "Add note"}
        </Button>
      </form>
      <div className="flex flex-col gap-2">
        {notes.length === 0 ? (
          <p className="text-xs text-muted-foreground">No notes yet.</p>
        ) : (
          notes.map((n) => (
            <div key={n.id} className="border-t border-border pt-2 text-sm">
              <p>{n.content}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {n.author ? `${n.author} · ` : ""}
                {new Date(n.created_at).toLocaleString()}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function AddSenderForm({ onCreated }: { onCreated: (sender: Sender) => void }) {
  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [email, setEmail] = useState("");
  const [portfolioUrl, setPortfolioUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Name is required.");
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
      setError(err instanceof ApiError ? err.message : "Failed to add teammate.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-wrap items-end gap-3 rounded-md border border-border p-3">
      <div>
        <Label>Name *</Label>
        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Jordan Lee" />
      </div>
      <div>
        <Label>Title</Label>
        <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Web Developer" />
      </div>
      <div>
        <Label>Email</Label>
        <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
      </div>
      <div>
        <Label>Portfolio / contact link</Label>
        <Input value={portfolioUrl} onChange={(e) => setPortfolioUrl(e.target.value)} placeholder="https://…" />
      </div>
      <Button type="submit" size="sm" disabled={saving}>
        {saving ? "Adding…" : "Add teammate"}
      </Button>
      {error && <span className="text-sm text-red-400">{error}</span>}
    </form>
  );
}
