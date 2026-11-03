"use client";

import Link from "next/link";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft } from "lucide-react";

import { ActivityTab } from "@/components/lead/activity-tab";
import { AuditTab } from "@/components/lead/audit-tab";
import { DocumentsTab } from "@/components/lead/documents-tab";
import { LeadHeader } from "@/components/lead/lead-header";
import type { ScoreReveal } from "@/components/lead/score-grade";
import { OutreachTab } from "@/components/lead/outreach-tab";
import { OverviewTab } from "@/components/lead/overview-tab";
import { DemoNotice } from "@/components/shell/page-header";
import { Card } from "@/components/ui/card";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingRegion, Skeleton, SkeletonRows } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { api, ApiError } from "@/lib/api";
import { isDemoMode } from "@/lib/runtime";
import type { BusinessDetail, ContractGenerateRequest, LeadStatus, Sender } from "@/lib/types";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "audit", label: "Audit" },
  { id: "outreach", label: "Outreach" },
  { id: "activity", label: "Activity" },
  { id: "documents", label: "Documents" },
] as const;

type TabId = (typeof TABS)[number]["id"];

function isTab(value: string | null): value is TabId {
  return TABS.some((tab) => tab.id === value);
}

const SENDER_KEY = "prospectos_sender_id";

function message(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}

export default function ProspectDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const confirm = useConfirm();
  const businessId = params.id;

  const tabParam = searchParams.get("tab");
  const activeTab: TabId = isTab(tabParam) ? tabParam : "overview";

  const [business, setBusiness] = useState<BusinessDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const toast = useToast();
  const [auditing, setAuditing] = useState(false);
  // Set only when someone runs an audit here; the header counts the score up.
  const [scoreReveal, setScoreReveal] = useState<ScoreReveal | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generatingBrief, setGeneratingBrief] = useState(false);
  const [visualBrief, setVisualBrief] = useState<string | null>(null);
  const [generatingContract, setGeneratingContract] = useState(false);
  const [angle, setAngle] = useState("");
  const [senders, setSenders] = useState<Sender[]>([]);
  const [senderId, setSenderId] = useState("");
  const [gmail, setGmail] = useState<{ connected: boolean; email: string | null }>({ connected: false, email: null });
  const [busyDraftId, setBusyDraftId] = useState<string | null>(null);

  const load = useCallback(() => {
    api
      .getBusiness(businessId)
      .then((detail) => {
        setBusiness(detail);
        setLoadError(null);
      })
      .catch((err) => setLoadError(message(err, "The API didn't answer. Check that it's running, then try again.")));
  }, [businessId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    api.gmailStatus().then(setGmail).catch(() => {});
    if (isDemoMode) return;
    api
      .listSenders()
      .then((list) => {
        setSenders(list);
        // Remember the last sender per browser so a teammate isn't reselected on every lead.
        let remembered: string | null = null;
        try {
          remembered = localStorage.getItem(SENDER_KEY);
        } catch {}
        if (remembered && list.some((sender) => sender.id === remembered)) setSenderId(remembered);
        else if (list.length > 0) setSenderId(list[0].id);
      })
      // Drafts can still be written without a sender; they just go unsigned.
      .catch(() => {});
  }, []);

  function changeSender(id: string) {
    setSenderId(id);
    try {
      localStorage.setItem(SENDER_KEY, id);
    } catch {}
  }

  function selectTab(tab: TabId) {
    router.replace(tab === "overview" ? pathname : `${pathname}?tab=${tab}`, { scroll: false });
  }

  async function handleRunAudit() {
    setAuditing(true);
    const before = business?.latest_audit?.overall_opportunity_score ?? null;
    try {
      await api.runAudit(businessId);
      try {
        // Set the new detail and the reveal in one render, so the header
        // never paints the new score before it starts counting up to it.
        const detail = await api.getBusiness(businessId);
        setBusiness(detail);
        setLoadError(null);
        setScoreReveal((current) => ({ from: before, key: (current?.key ?? 0) + 1 }));
      } catch {
        load();
      }
      toast(isDemoMode ? "Audit replayed." : "Audit finished.");
    } catch (err) {
      toast(message(err, "The audit didn't finish. Check the website address and try again."), "error");
    } finally {
      setAuditing(false);
    }
  }

  async function handleGenerateOutreach() {
    if (isDemoMode) {
      selectTab("outreach");
      return;
    }
    setGenerating(true);
    try {
      await api.generateOutreach(businessId, { angle: angle || undefined, sender_id: senderId || undefined });
      load();
      selectTab("outreach");
      toast("Draft written. It waits for approval before anything is sent.");
    } catch (err) {
      toast(message(err, "The draft couldn't be written. Try again."), "error");
    } finally {
      setGenerating(false);
    }
  }

  async function handleGenerateBrief() {
    if (isDemoMode) {
      setVisualBrief(
        "Prepared demo brief: build the concept around the primary, evidence-backed opportunity and keep it to one focused page. No AI service was called."
      );
      return;
    }
    setGeneratingBrief(true);
    try {
      const result = await api.generateVisualBrief(businessId);
      setVisualBrief(result.content);
    } catch (err) {
      toast(message(err, "The visual brief couldn't be written. Try again."), "error");
    } finally {
      setGeneratingBrief(false);
    }
  }

  async function handleGenerateContract(request: ContractGenerateRequest) {
    setGeneratingContract(true);
    try {
      await api.generateContract(businessId, request);
      load();
    } catch (err) {
      toast(message(err, "The document couldn't be created. Try again."), "error");
    } finally {
      setGeneratingContract(false);
    }
  }

  async function handleApproveDraft(draftId: string) {
    setBusyDraftId(draftId);
    try {
      await api.approveOutreach(draftId);
      load();
      toast("Draft approved. It can go out on its own or in a batch.");
    } catch (err) {
      toast(message(err, "The draft couldn't be approved. Try again."), "error");
    } finally {
      setBusyDraftId(null);
    }
  }

  async function handleSendDraft(draftId: string) {
    const ok = await confirm({
      title: "Send this email now?",
      body: `It goes to ${business?.email ?? "the lead"} from your connected Gmail account. This cannot be unsent.`,
      confirmLabel: "Send email",
    });
    if (!ok) return;
    setBusyDraftId(draftId);
    try {
      const sent = await api.sendOutreach(draftId);
      load();
      toast(`Email sent to ${sent.to}.`);
    } catch (err) {
      toast(message(err, "The email wasn't sent. Check the Gmail connection and try again."), "error");
    } finally {
      setBusyDraftId(null);
    }
  }

  async function handleMove(status: LeadStatus, note: string): Promise<boolean> {
    try {
      await api.changeStatus(businessId, { status, note: note || undefined });
      load();
      return true;
    } catch (err) {
      toast(message(err, "The stage couldn't be changed. Try again."), "error");
      return false;
    }
  }

  async function handleDelete() {
    const ok = await confirm({
      title: `Delete ${business?.name ?? "this lead"}?`,
      body: "Its audits, drafts, notes and stage history are deleted with it. This cannot be undone.",
      confirmLabel: "Delete lead",
      tone: "danger",
    });
    if (!ok) return;
    try {
      await api.deleteBusiness(businessId);
      toast(`Deleted ${business?.name ?? "the lead"}.`);
      router.push("/prospects");
    } catch (err) {
      toast(message(err, "The lead couldn't be deleted. Try again."), "error");
    }
  }

  if (!business) {
    return (
      <div className="flex flex-col gap-5">
        <Link
          href="/prospects"
          className="focus-ring -ml-1 inline-flex w-fit items-center gap-1.5 rounded-control px-1 py-0.5 text-[13px] text-graphite hover:text-ink"
        >
          <ArrowLeft size={14} aria-hidden="true" />
          Leads
        </Link>
        {loadError ? (
          <ErrorState title="This lead didn't load" body={loadError} onRetry={load} />
        ) : (
          <LoadingRegion label="Loading lead" className="flex flex-col gap-6">
            <div className="space-y-3">
              <Skeleton className="h-8 w-72 max-w-full" />
              <Skeleton className="h-3.5 w-48" />
            </div>
            <Card className="grid gap-6 p-5 sm:grid-cols-[auto_1fr]">
              <Skeleton className="h-20 w-24" />
              <div className="space-y-3">
                <Skeleton className="h-3.5 w-40" />
                <Skeleton className="h-3 w-full" />
              </div>
            </Card>
            <Skeleton className="h-9 w-full max-w-md" />
            <SkeletonRows rows={3} />
          </LoadingRegion>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <DemoNotice>
        This lead and its audit are fictional samples. Replaying the audit and previewing drafts never reaches a real
        website, AI service or inbox.
      </DemoNotice>

      <LeadHeader
        business={business}
        demo={isDemoMode}
        auditing={auditing}
        scoreReveal={scoreReveal}
        generating={generating}
        onGenerate={handleGenerateOutreach}
        onAudit={handleRunAudit}
        onMove={handleMove}
        onDelete={handleDelete}
      />

      <div>
        <Tabs active={activeTab} onSelect={selectTab} />
        <div role="tabpanel" id={`panel-${activeTab}`} aria-labelledby={`tab-${activeTab}`} className="pt-6">
          {activeTab === "overview" && (
            <OverviewTab
              business={business}
              onShowAudit={() => selectTab("audit")}
              onRunAudit={handleRunAudit}
              auditing={auditing}
              visualBrief={visualBrief}
              generatingBrief={generatingBrief}
              onGenerateBrief={handleGenerateBrief}
            />
          )}
          {activeTab === "audit" && (
            <AuditTab audits={business.audits} onRunAudit={handleRunAudit} auditing={auditing} demo={isDemoMode} />
          )}
          {activeTab === "outreach" && (
            <OutreachTab
              business={business}
              demo={isDemoMode}
              gmail={gmail}
              senders={senders}
              senderId={senderId}
              onSenderChange={changeSender}
              onSenderCreated={(sender) => {
                setSenders((list) => [...list, sender]);
                changeSender(sender.id);
              }}
              angle={angle}
              onAngleChange={setAngle}
              generating={generating}
              onGenerate={handleGenerateOutreach}
              busyDraftId={busyDraftId}
              onApprove={handleApproveDraft}
              onSend={handleSendDraft}
            />
          )}
          {activeTab === "activity" && <ActivityTab business={business} demo={isDemoMode} onChanged={load} />}
          {activeTab === "documents" && (
            <DocumentsTab
              contracts={business.contracts}
              demo={isDemoMode}
              senders={senders}
              senderId={senderId}
              onSenderChange={changeSender}
              generating={generatingContract}
              onGenerate={handleGenerateContract}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// WAI-ARIA tabs: one tab stop, arrow keys move between tabs and select them.
function Tabs({ active, onSelect }: { active: TabId; onSelect: (tab: TabId) => void }) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  function onKeyDown(event: React.KeyboardEvent, index: number) {
    let next = -1;
    if (event.key === "ArrowRight") next = (index + 1) % TABS.length;
    else if (event.key === "ArrowLeft") next = (index - 1 + TABS.length) % TABS.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = TABS.length - 1;
    if (next < 0) return;
    event.preventDefault();
    refs.current[next]?.focus();
    onSelect(TABS[next].id);
  }

  return (
    // The baseline is an inset shadow, not a border, so the selected tab's
    // underline can sit on it without overflowing the scroll container.
    <div
      role="tablist"
      aria-label="Lead sections"
      className="-mx-4 flex overflow-x-auto px-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden shadow-[inset_0_-1px_0_rgb(var(--rule))] sm:mx-0 sm:px-0"
    >
      {TABS.map((tab, index) => {
        const selected = tab.id === active;
        return (
          <button
            key={tab.id}
            ref={(node) => {
              refs.current[index] = node;
            }}
            id={`tab-${tab.id}`}
            type="button"
            role="tab"
            aria-selected={selected}
            aria-controls={`panel-${tab.id}`}
            tabIndex={selected ? 0 : -1}
            onClick={() => onSelect(tab.id)}
            onKeyDown={(event) => onKeyDown(event, index)}
            className={cn(
              "focus-ring relative shrink-0 rounded-t-control border-b-2 px-3 py-2.5 text-sm transition-colors duration-fast ease-assay",
              selected ? "border-ink font-medium text-ink" : "border-transparent text-graphite hover:text-ink"
            )}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
