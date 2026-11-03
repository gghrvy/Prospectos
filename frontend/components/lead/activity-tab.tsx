"use client";

import { useState } from "react";

import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { activityTime } from "@/lib/activity";
import { api, ApiError } from "@/lib/api";
import type { BusinessDetail } from "@/lib/types";

export function ActivityTab({
  business,
  demo,
  onChanged,
}: {
  business: BusinessDetail;
  demo: boolean;
  onChanged: () => void;
}) {
  const history = [...business.status_history].sort((a, b) => b.created_at.localeCompare(a.created_at));
  const notes = [...business.notes].sort((a, b) => b.created_at.localeCompare(a.created_at));

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Stage history</CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <p className="text-sm leading-6 text-graphite">No stage changes yet. Each move is listed here with its date and note.</p>
          ) : (
            <ol className="flex flex-col">
              {history.map((entry, i) => (
                <li key={entry.id} className="relative flex gap-4 pb-5 last:pb-0">
                  {i < history.length - 1 && (
                    <span className="absolute bottom-0 left-[3.5px] top-4 w-px bg-rule" aria-hidden="true" />
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                      <StatusBadge status={entry.status} />
                      <time dateTime={entry.created_at} className="text-xs tabular-nums text-graphite">
                        {activityTime(entry.created_at)}
                      </time>
                    </div>
                    {entry.note && <p className="mt-1 pl-[14px] text-sm leading-6 text-graphite">{entry.note}</p>}
                  </div>
                </li>
              ))}
            </ol>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notes</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {demo ? (
            <p className="text-sm text-graphite">Notes are turned off in the public demo.</p>
          ) : (
            <NoteForm businessId={business.id} onAdded={onChanged} />
          )}
          {notes.length === 0 ? (
            !demo && <p className="text-sm leading-6 text-graphite">No notes yet. Notes are for anything worth remembering about this lead.</p>
          ) : (
            <ul className="flex flex-col divide-y divide-rule/70">
              {notes.map((note) => (
                <li key={note.id} className="py-3 first:pt-0 last:pb-0">
                  <p className="whitespace-pre-wrap text-sm leading-6 text-ink">{note.content}</p>
                  <p className="mt-1 text-xs text-graphite">
                    {note.author ? `${note.author}, ` : ""}
                    {activityTime(note.created_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function NoteForm({ businessId, onAdded }: { businessId: string; onAdded: () => void }) {
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!content.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await api.addNote(businessId, { content });
      setContent("");
      onAdded();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The note couldn't be saved. Try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-2">
      <Label htmlFor="note-content" className="sr-only">
        New note
      </Label>
      <Textarea
        id="note-content"
        rows={3}
        value={content}
        onChange={(event) => setContent(event.target.value)}
        placeholder="Add a note, e.g. spoke to the owner, call back Friday"
      />
      {error && (
        <p role="alert" className="text-[13px] text-brick">
          {error}
        </p>
      )}
      <Button type="submit" size="sm" variant="outline" disabled={saving || !content.trim()} className="self-start">
        {saving ? "Saving…" : "Add note"}
      </Button>
    </form>
  );
}
