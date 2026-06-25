"use server";

import { sequence_by_id } from "./sequence";
import { screen_by_id } from "./screen";

/* =======================
 * Public API
 * ======================= */

type SequenceCache = Record<string, any>;
const sequenceCache: SequenceCache = {};

export async function playback(screen_id: string) {
  const screen = await screen_by_id(screen_id);
  const sequence_id = await check_sequence_from_screen(screen);

  const getSequenceCached = async (id: string) => {
    if (!sequenceCache[id]) {
      sequenceCache[id] = await sequence_by_id(id);
    }
    return sequenceCache[id];
  };

  const rootSequence = await getSequenceCached(sequence_id);

  const results = await resolveSequencePlayback(
    rootSequence,
    screen,
    getSequenceCached
  );

  return results;
}


/* =======================
 * Helpers
 * ======================= */

async function check_sequence_from_screen(screen: any): Promise<string> {
  const data = screen.data || {};
  const sequence_id = data.sequenceIdOverride || data.sequenceId;

  if (!sequence_id) {
    throw new Error(
      `Sequence ID not found for screen: ${screen.id || "unknown"}`
    );
  }

  return sequence_id;
}

type InnerCursorMap = Record<string, number>;

type ResolvedItem = {
  screenId: string;
  libraryItemId: string;
  label: string;
  blobId: string | null;
};

/* =======================
 * Condition & Time
 * ======================= */

function passTimeWindow(item: any, now = Date.now()): boolean {
  const data = item.data || {};

  const start =
    data.startMillis == null ? now : Number(data.startMillis);

  const end =
    data.endMillis == null ? Infinity : Number(data.endMillis);

  return now >= start && now <= end;
}

function passCondition(item: any, screen: any): boolean {
  const condition = item.data?.condition;
  if (!condition) return true;

  function evalSimple(expr: string): boolean {
    const match = expr.match(
      /^\s*([\w.]+)\s*(==|!=)\s*"([^"]*)"\s*$/
    );
    if (!match) return false;

    const [, key, operator, expected] = match;
    const actual = screen.data?.[key];

    if (actual == null) return false;

    if (operator === "==") {
      return String(actual) === expected;
    }
    if (operator === "!=") {
      return String(actual) !== expected;
    }
    return false;
  }

  // OR
  const orGroups = condition.split("||");

  for (const orGroup of orGroups) {
    // AND
    const andConds = orGroup.split("&&");
    const allPass = andConds.every((expr: string) =>
      evalSimple(expr.trim())
    );
    if (allPass) return true;
  }

  return false;
}

function itemPass(item: any, screen: any): boolean {
  return (
    passTimeWindow(item) &&
    passCondition(item, screen)
  );
}

/* =======================
 * Media extractor
 * ======================= */

function extractMediaInfo(item: any) {
  const label = item.data?.label ?? null;

  const blobId =
    item.resources?.find(
      (r: any) =>
        r.data?.blobId &&
        (r.data?.contentType?.startsWith("video") ||
         r.data?.contentType?.startsWith("image"))
    )?.data?.blobId ?? null;

  return { label, blobId };
}

/* =======================
 * Resolver (Item / InnerSequence)
 * ======================= */

async function resolveItem(
  item: any,
  screen: any,
  cursorMap: InnerCursorMap,
  getSequenceById: (id: string) => Promise<any>
): Promise<ResolvedItem | null> {

  if (!itemPass(item, screen)) return null;

  // case: library item
  if (item.data?.libraryItemId) {
    const { label, blobId } = extractMediaInfo(item);

    return {
      screenId: screen.id,
      libraryItemId: item.data.libraryItemId,
      label,
      blobId,
    };
  }

  // case: inner sequence
  if (item.data?.innerSequenceId) {
    const innerSeq = await getSequenceById(item.data.innerSequenceId);
    return resolveInnerSequence(
      innerSeq,
      screen,
      cursorMap,
      getSequenceById
    );
  }

  return null;
}

async function resolveInnerSequence(
  innerSequence: any,
  screen: any,
  cursorMap: InnerCursorMap,
  getSequenceById: (id: string) => Promise<any>
): Promise<ResolvedItem | null> {

  const items =
    innerSequence?.stacks?.flatMap((s: any) => s.items || []) || [];

  if (items.length === 0) return null;

  const seqId = innerSequence.id;
  let cursor = cursorMap[seqId] ?? 0;

  for (let i = 0; i < items.length; i++) {
    const index = (cursor + i) % items.length;
    const item = items[index];

    if (!itemPass(item, screen)) continue;

    cursorMap[seqId] = (index + 1) % items.length;

    if (item.data?.libraryItemId) {
      const { label, blobId } = extractMediaInfo(item);

      return {
        screenId: screen.id,
        libraryItemId: item.data.libraryItemId,
        label,
        blobId,
      };
    }

    if (item.data?.innerSequenceId) {
      const nested = await getSequenceById(item.data.innerSequenceId);
      const resolved = await resolveInnerSequence(
        nested,
        screen,
        cursorMap,
        getSequenceById
      );
      if (resolved) return resolved;
    }
  }

  return null;
}

/* =======================
 * Main Sequence Resolver
 * ======================= */

export async function resolveSequencePlayback(
  sequence: any,
  screen: any,
  getSequenceById: (id: string) => Promise<any>
): Promise<ResolvedItem[]> {

  const results: ResolvedItem[] = [];
  const cursorMap: InnerCursorMap = {}; // memory-only per screen

  for (const stack of sequence?.stacks || []) {
    let resolved: ResolvedItem | null = null;

    for (const item of stack.items || []) {
      resolved = await resolveItem(
        item,
        screen,
        cursorMap,
        getSequenceById
      );
      if (resolved) break;
    }

    if (resolved) {
      results.push(resolved);
    }
  }

  return results;
}
