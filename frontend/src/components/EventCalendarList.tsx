"use client";

import { useState } from "react";
import Link from "next/link";

export interface CalendarEvent {
  id: number;
  title: string;
  date_time: string;
  location: string;
  visibility?: string;
  status?: string;
}

interface EventCalendarListProps {
  events: CalendarEvent[];
  primaryColour?: string;
  accentColour?: string;
}

const DAY_HEADERS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

function isSameDay(iso: string, year: number, month: number, day: number): boolean {
  const d = new Date(iso);
  return d.getFullYear() === year && d.getMonth() === month && d.getDate() === day;
}

/** Build a grid of cells for a given month (0-indexed). Returns rows of 7, with null for empty cells. */
function buildCalendarGrid(year: number, month: number): (number | null)[][] {
  const firstDay = new Date(year, month, 1).getDay(); // 0=Sun
  // Convert to Mon-first: Mon=0, Tue=1, ..., Sun=6
  const offset = (firstDay + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const cells: (number | null)[] = [
    ...Array(offset).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];
  // Pad to complete last row
  while (cells.length % 7 !== 0) cells.push(null);

  const rows: (number | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) {
    rows.push(cells.slice(i, i + 7));
  }
  return rows;
}

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function EventCalendarList({
  events,
  primaryColour = "#1a73e8",
  accentColour = "#ff6d00",
}: EventCalendarListProps) {
  const now = new Date();
  const [view, setView] = useState<"calendar" | "list">("list");
  const [calYear, setCalYear] = useState(now.getFullYear());
  const [calMonth, setCalMonth] = useState(now.getMonth());

  function prevMonth() {
    if (calMonth === 0) { setCalYear(y => y - 1); setCalMonth(11); }
    else setCalMonth(m => m - 1);
  }

  function nextMonth() {
    if (calMonth === 11) { setCalYear(y => y + 1); setCalMonth(0); }
    else setCalMonth(m => m + 1);
  }

  const rows = buildCalendarGrid(calYear, calMonth);
  const monthEvents = events.filter(ev => {
    const d = new Date(ev.date_time);
    return d.getFullYear() === calYear && d.getMonth() === calMonth;
  });

  return (
    <div>
      {/* View toggle */}
      <div className="flex items-center gap-2 mb-6">
        <button
          onClick={() => setView("list")}
          className="px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors"
          style={
            view === "list"
              ? { backgroundColor: primaryColour, color: "#fff", borderColor: primaryColour }
              : { color: "#6b7280", borderColor: "#d1d5db" }
          }
        >
          List
        </button>
        <button
          onClick={() => setView("calendar")}
          className="px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors"
          style={
            view === "calendar"
              ? { backgroundColor: primaryColour, color: "#fff", borderColor: primaryColour }
              : { color: "#6b7280", borderColor: "#d1d5db" }
          }
        >
          Calendar
        </button>
      </div>

      {/* LIST VIEW */}
      {view === "list" && (
        <div>
          {events.length === 0 ? (
            <div className="text-center py-16 text-zinc-500 bg-zinc-50 dark:bg-zinc-900 rounded-xl">
              <p className="text-lg mb-2">No upcoming events</p>
              <p className="text-sm">Check back soon.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {events.map((ev) => (
                <Link
                  key={ev.id}
                  href={`/events/${ev.id}`}
                  className="flex items-start gap-4 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4 bg-white dark:bg-zinc-800 hover:shadow-sm transition-shadow block"
                >
                  <div
                    className="shrink-0 w-14 text-center rounded-lg py-1.5"
                    style={{ backgroundColor: `${primaryColour}18` }}
                  >
                    <p className="text-xs font-semibold uppercase" style={{ color: primaryColour }}>
                      {new Date(ev.date_time).toLocaleDateString("en-GB", { month: "short" })}
                    </p>
                    <p className="text-2xl font-bold leading-tight" style={{ color: primaryColour }}>
                      {new Date(ev.date_time).getDate()}
                    </p>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100 truncate">{ev.title}</p>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-0.5">
                      {formatDate(ev.date_time)} · {formatTime(ev.date_time)}
                    </p>
                    {ev.location && (
                      <p className="text-sm text-zinc-400 dark:text-zinc-500 truncate">{ev.location}</p>
                    )}
                    {ev.visibility === "members_only" && (
                      <span
                        className="inline-block mt-1 text-xs font-medium px-2 py-0.5 rounded"
                        style={{ backgroundColor: `${accentColour}20`, color: accentColour }}
                      >
                        Members only
                      </span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      {/* CALENDAR VIEW */}
      {view === "calendar" && (
        <div>
          {/* Month navigation */}
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={prevMonth}
              className="p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-400"
            >
              ‹
            </button>
            <h2 className="text-base font-semibold text-zinc-800 dark:text-zinc-200">
              {MONTH_NAMES[calMonth]} {calYear}
            </h2>
            <button
              onClick={nextMonth}
              className="p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-400"
            >
              ›
            </button>
          </div>

          {/* Calendar grid — hidden on mobile, shown on sm+ */}
          <div className="hidden sm:block border border-zinc-200 dark:border-zinc-700 rounded-xl overflow-hidden">
            {/* Day headers */}
            <div className="grid grid-cols-7 bg-zinc-50 dark:bg-zinc-800 border-b border-zinc-200 dark:border-zinc-700">
              {DAY_HEADERS.map((d) => (
                <div key={d} className="px-2 py-2 text-xs font-medium text-center text-zinc-500 dark:text-zinc-400">
                  {d}
                </div>
              ))}
            </div>
            {/* Weeks */}
            {rows.map((row, ri) => (
              <div key={ri} className="grid grid-cols-7 divide-x divide-zinc-100 dark:divide-zinc-700 border-b border-zinc-100 dark:border-zinc-700 last:border-b-0">
                {row.map((day, di) => {
                  const dayEvents = day
                    ? events.filter((ev) => isSameDay(ev.date_time, calYear, calMonth, day))
                    : [];
                  const isToday =
                    day === now.getDate() &&
                    calYear === now.getFullYear() &&
                    calMonth === now.getMonth();
                  return (
                    <div key={di} className="min-h-[80px] p-1.5 bg-white dark:bg-zinc-900">
                      {day && (
                        <>
                          <span
                            className={`text-xs font-medium inline-block w-6 h-6 flex items-center justify-center rounded-full ${
                              isToday ? "text-white" : "text-zinc-600 dark:text-zinc-400"
                            }`}
                            style={isToday ? { backgroundColor: primaryColour } : {}}
                          >
                            {day}
                          </span>
                          <div className="mt-0.5 space-y-0.5">
                            {dayEvents.map((ev) => (
                              <Link
                                key={ev.id}
                                href={`/events/${ev.id}`}
                                className="block text-xs px-1 py-0.5 rounded truncate text-white leading-tight"
                                style={{ backgroundColor: primaryColour }}
                                title={ev.title}
                              >
                                {ev.title}
                              </Link>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Agenda for mobile (sm:hidden) */}
          <div className="sm:hidden">
            {monthEvents.length === 0 ? (
              <div className="text-center py-8 text-zinc-400 text-sm">
                No events in {MONTH_NAMES[calMonth]} {calYear}
              </div>
            ) : (
              <div className="space-y-2">
                {monthEvents.map((ev) => (
                  <Link
                    key={ev.id}
                    href={`/events/${ev.id}`}
                    className="flex items-center gap-3 border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 bg-white dark:bg-zinc-800 block"
                  >
                    <div
                      className="shrink-0 w-10 text-center rounded py-1"
                      style={{ backgroundColor: `${primaryColour}18` }}
                    >
                      <p className="text-xl font-bold leading-tight" style={{ color: primaryColour }}>
                        {new Date(ev.date_time).getDate()}
                      </p>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-zinc-900 dark:text-zinc-100 truncate text-sm">{ev.title}</p>
                      <p className="text-xs text-zinc-500">{formatTime(ev.date_time)}</p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
