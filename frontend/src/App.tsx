import {
  Bookmark,
  Building2,
  CalendarDays,
  ChartNoAxesCombined,
  CircleUser,
  Clock3,
  CloudUpload,
  Copy,
  FileText,
  History,
  Layers3,
  Library,
  Menu,
  MessageCircle,
  PanelLeftClose,
  PanelLeftOpen,
  Paperclip,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  Users,
  X
} from "lucide-react";
import { ChangeEvent, DragEvent, FormEvent, KeyboardEvent, ReactNode, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";

import { askQuestion, listDocuments, uploadDocument } from "./api";
import "./App.css";
import { appConfig } from "./config";
import type { DocumentRecord, QAAskResponse } from "./types";

const SUPPORTED_TYPES = ".pdf,.docx,.txt";

type FocusMode = "balanced" | "precision" | "broad";
type KnowledgeSource = "all" | "pdf" | "docx" | "txt";
type DateRange = "all" | "7d" | "30d" | "90d";
type NavItemId =
  | "ask-ai"
  | "source-library"
  | "department-knowledge"
  | "answer-history"
  | "access-control"
  | "admin-analytics";
type FeedbackState = "good" | "not-useful";

type NavItem = {
  id: NavItemId;
  label: string;
  implemented: boolean;
  icon: ReactNode;
  tone: "ai" | "knowledge" | "history" | "security" | "analytics";
};

type ConversationEntry = {
  id: string;
  question: string;
  askedAt: string;
  response: QAAskResponse;
  responseMs: number;
};

const NAV_ITEMS: NavItem[] = [
  {
    id: "ask-ai",
    label: "Ask AI",
    implemented: true,
    icon: <Sparkles size={18} strokeWidth={1.8} />,
    tone: "ai"
  },
  {
    id: "source-library",
    label: "Source Library",
    implemented: true,
    icon: <Library size={18} strokeWidth={1.8} />,
    tone: "knowledge"
  },
  {
    id: "department-knowledge",
    label: "Department Knowledge",
    implemented: false,
    icon: <Building2 size={18} strokeWidth={1.8} />,
    tone: "knowledge"
  },
  {
    id: "answer-history",
    label: "Answer History",
    implemented: true,
    icon: <History size={18} strokeWidth={1.8} />,
    tone: "history"
  },
  {
    id: "access-control",
    label: "Access Control",
    implemented: false,
    icon: <ShieldCheck size={18} strokeWidth={1.8} />,
    tone: "security"
  },
  {
    id: "admin-analytics",
    label: "Admin Analytics",
    implemented: false,
    icon: <ChartNoAxesCombined size={18} strokeWidth={1.8} />,
    tone: "analytics"
  }
];

const DEFAULT_SUGGESTED_QUESTIONS = [
  "What is our remote work policy?",
  "How do I request budget approval?",
  "What tools do we use for analytics?",
  "Where can I find the OKR process?"
];

const INTEGRATIONS = [
  { key: "documents", label: "Documents", icon: <FileText size={14} />, status: "connected" as const },
  { key: "types", label: "PDF / DOCX / TXT", icon: <Library size={14} />, status: "connected" as const }
];

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatRelativeTime(isoDate: string): string {
  const value = new Date(isoDate).getTime();
  const delta = Date.now() - value;
  const minute = 60_000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (delta < minute) {
    return "just now";
  }
  if (delta < hour) {
    return `${Math.floor(delta / minute)}m ago`;
  }
  if (delta < day) {
    return `${Math.floor(delta / hour)}h ago`;
  }
  return `${Math.floor(delta / day)}d ago`;
}

function getConfidenceScore(response: QAAskResponse): number | null {
  if (response.citations.length === 0) {
    return null;
  }
  const total = response.citations.reduce((sum, citation) => sum + citation.confidence_score, 0);
  return total / response.citations.length;
}

function getConfidenceLabel(score: number | null): "low" | "medium" | "high" | "n/a" {
  if (score === null) {
    return "n/a";
  }
  if (score >= 0.75) {
    return "high";
  }
  if (score >= 0.45) {
    return "medium";
  }
  return "low";
}

function getSourceType(mimeType: string | undefined): string {
  if (!mimeType) {
    return "Unknown";
  }
  if (mimeType.includes("pdf")) {
    return "PDF";
  }
  if (mimeType.includes("wordprocessingml")) {
    return "DOCX";
  }
  if (mimeType.includes("text/plain")) {
    return "TXT";
  }
  return mimeType;
}

function summarizeKeyPoints(answer: string): string[] {
  const normalized = normalizeAnswerForMarkdown(answer)
    .replace(/^\|.*\|$/gm, "")
    .replace(/^[-:| ]+$/gm, "")
    .replace(/\*\*/g, "")
    .replace(/`/g, "");

  const explicitBullets = normalized
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("- ") || line.startsWith("* ") || line.startsWith("• "))
    .map((line) => line.replace(/^[-*•]\s+/, ""));
  if (explicitBullets.length > 0) {
    return explicitBullets.slice(0, 4);
  }
  return normalized
    .split(/[.!?]\s+/)
    .map((sentence) => sentence.trim())
    .filter((sentence) => sentence.length > 20)
    .slice(0, 4);
}

function topicFromQuestion(question: string): string {
  const cleaned = question.replace(/[^\w\s]/g, "").trim();
  return cleaned.split(/\s+/).slice(0, 6).join(" ");
}

function buildFollowUps(entry: ConversationEntry | null): string[] {
  if (!entry) {
    return [];
  }
  const topic = topicFromQuestion(entry.question) || "this topic";
  return [
    `What are the key exceptions related to ${topic}?`,
    `Can you summarize the required steps for ${topic}?`,
    `Which document sections support ${topic}?`,
    `What should I do if ${topic} is unclear?`
  ];
}

function topKForMode(mode: FocusMode): number {
  if (mode === "precision") {
    return 4;
  }
  if (mode === "broad") {
    return 10;
  }
  return 6;
}

function toDocPromptLabel(documentName: string): string {
  const noExtension = documentName.replace(/\.(pdf|docx|txt)$/i, "");
  return noExtension.length > 48 ? `${noExtension.slice(0, 45)}...` : noExtension;
}

function isMarkdownTableRow(line: string): boolean {
  return /^\s*\|.*\|\s*$/.test(line.trim());
}

function normalizeAnswerForMarkdown(answer: string): string {
  const sanitized = answer
    .replace(/&lt;br\s*\/?&gt;/gi, "\n")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&amp;/gi, "&")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/\r\n?/g, "\n")
    .replace(/\\([|*_`])/g, "$1");
  const normalizedLines = sanitized.split("\n").map((line) => line.replace(/\s+$/g, ""));
  const output: string[] = [];
  let index = 0;

  while (index < normalizedLines.length) {
    const current = normalizedLines[index];

    if (isMarkdownTableRow(current)) {
      output.push(current.trim());
      index += 1;
      while (index < normalizedLines.length) {
        const candidate = normalizedLines[index];
        if (candidate.trim().length === 0) {
          index += 1;
          continue;
        }
        if (!isMarkdownTableRow(candidate)) {
          break;
        }
        output.push(candidate.trim());
        index += 1;
      }
      continue;
    }

    if (current.trim().length === 0) {
      const previous = output.length > 0 ? output[output.length - 1] : undefined;
      if (previous !== "") {
        output.push("");
      }
    } else {
      const normalizedLine = current.replace(/^\s*[•▪◦]\s+/, "- ");
      output.push(normalizedLine);
    }
    index += 1;
  }

  return output.join("\n").trim();
}

function SourceTypeIcon({ sourceType }: { sourceType: string }) {
  return (
    <span className={`source-type-icon tone-${sourceType.toLowerCase()}`}>
      <FileText size={14} strokeWidth={1.8} />
    </span>
  );
}

export function App() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [documentsError, setDocumentsError] = useState<string | null>(null);

  const [selectedDocumentIds, setSelectedDocumentIds] = useState<Set<string>>(new Set());
  const [documentQuery, setDocumentQuery] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("all");
  const [dateRangeFilter, setDateRangeFilter] = useState<DateRange>("all");
  const [sourceFilter, setSourceFilter] = useState<KnowledgeSource>("all");

  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [qaError, setQaError] = useState<string | null>(null);
  const [conversation, setConversation] = useState<ConversationEntry[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [feedbackByConversation, setFeedbackByConversation] = useState<Record<string, FeedbackState>>({});
  const [bookmarkedConversations, setBookmarkedConversations] = useState<Set<string>>(new Set());
  const [copyMessage, setCopyMessage] = useState<string | null>(null);

  const [focusMode, setFocusMode] = useState<FocusMode>("balanced");
  const [activeView, setActiveView] = useState<NavItemId>("ask-ai");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [navNotice, setNavNotice] = useState<string | null>(null);
  const [futureHintTarget, setFutureHintTarget] = useState<"settings" | "profile" | null>(null);
  const futureHintTimerRef = useRef<number | null>(null);

  const documentById = useMemo(() => {
    return new Map(documents.map((document) => [document.document_id, document]));
  }, [documents]);

  const filteredDocuments = useMemo(() => {
    const normalized = documentQuery.trim().toLowerCase();
    const now = Date.now();
    const dateCutoffMs =
      dateRangeFilter === "7d"
        ? 7 * 24 * 60 * 60 * 1000
        : dateRangeFilter === "30d"
          ? 30 * 24 * 60 * 60 * 1000
          : dateRangeFilter === "90d"
            ? 90 * 24 * 60 * 60 * 1000
            : null;

    return documents.filter((document) => {
      const matchesQuery =
        !normalized ||
        [document.document_name, document.mime_type, document.document_id].join(" ").toLowerCase().includes(normalized);
      const sourceType = getSourceType(document.mime_type).toLowerCase() as KnowledgeSource;
      const matchesSource = sourceFilter === "all" || sourceType === sourceFilter;
      const matchesDate =
        dateCutoffMs === null || now - new Date(document.ingested_at).getTime() <= dateCutoffMs;
      return matchesQuery && matchesSource && matchesDate;
    });
  }, [documents, documentQuery, sourceFilter, dateRangeFilter]);

  const activeConversation = useMemo(() => {
    if (activeConversationId) {
      return conversation.find((entry) => entry.id === activeConversationId) ?? null;
    }
    return conversation.length > 0 ? conversation[conversation.length - 1] : null;
  }, [conversation, activeConversationId]);

  const qaResponse = activeConversation?.response ?? null;
  const confidenceScore = qaResponse ? getConfidenceScore(qaResponse) : null;
  const confidenceLabel = getConfidenceLabel(confidenceScore);
  const keyPoints = qaResponse ? summarizeKeyPoints(qaResponse.answer) : [];
  const followUpQuestions = buildFollowUps(activeConversation);
  const suggestedQuestions = useMemo(() => {
    const scopedDocuments = documents.filter((document) => selectedDocumentIds.has(document.document_id));
    if (scopedDocuments.length === 0) {
      return DEFAULT_SUGGESTED_QUESTIONS;
    }

    if (scopedDocuments.length === 1) {
      const target = toDocPromptLabel(scopedDocuments[0].document_name);
      return [
        `Summarize the key points in ${target}.`,
        `What actions or decisions are required in ${target}?`,
        `Which sections in ${target} mention timelines or deadlines?`,
        `What are the risks or constraints noted in ${target}?`
      ];
    }

    const first = toDocPromptLabel(scopedDocuments[0].document_name);
    const second = toDocPromptLabel(scopedDocuments[1].document_name);
    return [
      `Compare the key points between ${first} and ${second}.`,
      `What overlaps and differences exist across the selected documents?`,
      `Which selected documents define approval steps or ownership?`,
      `Create a concise summary of the selected documents.`
    ];
  }, [documents, selectedDocumentIds]);

  const citationByChunkId = useMemo(() => {
    const citations = new Map<string, QAAskResponse["citations"][number]>();
    if (!qaResponse) {
      return citations;
    }
    for (const citation of qaResponse.citations) {
      if (!citations.has(citation.chunk_id)) {
        citations.set(citation.chunk_id, citation);
      }
    }
    return citations;
  }, [qaResponse]);

  useEffect(() => {
    void refreshDocuments();
  }, []);

  useEffect(() => {
    return () => {
      if (futureHintTimerRef.current !== null) {
        window.clearTimeout(futureHintTimerRef.current);
      }
    };
  }, []);

  async function refreshDocuments(): Promise<void> {
    setLoadingDocuments(true);
    setDocumentsError(null);
    try {
      const payload = await listDocuments();
      setDocuments(payload);
      const validIds = new Set(payload.map((document) => document.document_id));
      setSelectedDocumentIds((current) => {
        const next = new Set<string>();
        for (const id of current) {
          if (validIds.has(id)) {
            next.add(id);
          }
        }
        return next;
      });
    } catch (error) {
      setDocumentsError(error instanceof Error ? error.message : "Failed to load documents");
    } finally {
      setLoadingDocuments(false);
    }
  }

  function onSelectFile(event: ChangeEvent<HTMLInputElement>): void {
    setUploadError(null);
    setUploadProgress(null);
    const file = event.target.files?.[0] ?? null;
    setUploadFile(file);
  }

  function onDropFile(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
    if (uploading) {
      return;
    }
    const file = event.dataTransfer.files?.[0] ?? null;
    if (!file) {
      return;
    }
    setUploadError(null);
    setUploadProgress(null);
    setUploadFile(file);
  }

  async function onUploadSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!uploadFile) {
      setUploadError("Select a PDF, DOCX, or TXT file before upload.");
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadProgress(0);
    try {
      await uploadDocument(uploadFile, (percent) => setUploadProgress(percent));
      setUploadFile(null);
      setUploadProgress(100);
      await refreshDocuments();
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function toggleDocumentSelection(documentId: string): void {
    setSelectedDocumentIds((current) => {
      const next = new Set(current);
      if (next.has(documentId)) {
        next.delete(documentId);
      } else {
        next.add(documentId);
      }
      return next;
    });
  }

  async function submitQuestion(rawQuestion: string): Promise<void> {
    const trimmedQuestion = rawQuestion.trim();
    if (!trimmedQuestion) {
      setQaError("Enter a question before asking.");
      return;
    }
    setQaError(null);
    setAsking(true);
    setCopyMessage(null);
    const startedAt = performance.now();
    try {
      const response = await askQuestion({
        query: trimmedQuestion,
        top_k: topKForMode(focusMode),
        document_ids: selectedDocumentIds.size > 0 ? Array.from(selectedDocumentIds) : undefined
      });
      const responseMs = Math.round(performance.now() - startedAt);
      const entry: ConversationEntry = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        question: trimmedQuestion,
        askedAt: new Date().toISOString(),
        response,
        responseMs
      };
      setConversation((current) => [...current, entry]);
      setActiveConversationId(entry.id);
      setQuestion("");
      setActiveView("ask-ai");
    } catch (error) {
      setQaError(error instanceof Error ? error.message : "Question request failed");
    } finally {
      setAsking(false);
    }
  }

  async function onAsk(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    await submitQuestion(question);
  }

  async function onQuestionKeyDown(event: KeyboardEvent<HTMLTextAreaElement>): Promise<void> {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      await submitQuestion(question);
    }
  }

  function clearFilters(): void {
    setDepartmentFilter("all");
    setDateRangeFilter("all");
    setSourceFilter("all");
    setDocumentQuery("");
  }

  function handleNavSelection(item: NavItem): void {
    if (!item.implemented) {
      setNavNotice(`${item.label} is not implemented in this build yet.`);
      return;
    }
    setNavNotice(null);
    setActiveView(item.id);
    setSidebarOpen(false);
  }

  async function copyAnswerText(): Promise<void> {
    if (!qaResponse) {
      return;
    }
    if (!navigator.clipboard) {
      setCopyMessage("Clipboard is unavailable in this browser.");
      return;
    }
    try {
      await navigator.clipboard.writeText(qaResponse.answer);
      setCopyMessage("Answer copied to clipboard.");
    } catch {
      setCopyMessage("Could not copy answer.");
    }
  }

  function markFeedback(state: FeedbackState): void {
    if (!activeConversation) {
      return;
    }
    setFeedbackByConversation((current) => ({ ...current, [activeConversation.id]: state }));
  }

  function toggleBookmark(): void {
    if (!activeConversation) {
      return;
    }
    setBookmarkedConversations((current) => {
      const next = new Set(current);
      if (next.has(activeConversation.id)) {
        next.delete(activeConversation.id);
      } else {
        next.add(activeConversation.id);
      }
      return next;
    });
  }

  function showFutureHint(target: "settings" | "profile"): void {
    setFutureHintTarget(target);
    if (futureHintTimerRef.current !== null) {
      window.clearTimeout(futureHintTimerRef.current);
    }
    futureHintTimerRef.current = window.setTimeout(() => {
      setFutureHintTarget(null);
      futureHintTimerRef.current = null;
    }, 1800);
  }

  return (
    <div className={`app-root ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      <aside
        className={`sidebar ${sidebarCollapsed ? "collapsed" : ""} ${sidebarOpen ? "open" : ""}`}
        aria-label="Primary navigation"
      >
        <div className="sidebar-top">
          <div className="brand-row">
            <button className="icon-button mobile-only" onClick={() => setSidebarOpen(false)} aria-label="Close menu">
              <X size={18} />
            </button>
            <div className="brand-badge" aria-hidden="true">
              <Sparkles size={20} strokeWidth={2} />
            </div>
            {!sidebarCollapsed && (
              <div>
                <p className="brand-name">Enterprise RAG Assistant</p>
                <p className="brand-subtitle">Enterprise Workspace</p>
              </div>
            )}
          </div>
        </div>

        <nav className="nav-list">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${activeView === item.id ? "active" : ""}`}
              onClick={() => handleNavSelection(item)}
              title={item.implemented ? item.label : `${item.label} (not implemented)`}
              aria-label={item.label}
            >
              <span className={`nav-icon tone-${item.tone}`} aria-hidden="true">
                {item.icon}
              </span>
              {!sidebarCollapsed && (
                <>
                  <span>{item.label}</span>
                  {!item.implemented && <span className="beta-tag">Future</span>}
                </>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          {!sidebarCollapsed && (
            <>
              <section className="sidebar-card">
                <p className="card-title">Plan</p>
                <p className="card-strong">Local Free Tier</p>
                <p className="card-muted">API: {appConfig.apiBaseUrl}</p>
                <p className="card-muted">Indexed docs: {documents.length}</p>
                <p className="card-muted">Selected scope: {selectedDocumentIds.size}</p>
              </section>
              <section className="profile-row">
                <div className="avatar">
                  <CircleUser size={19} />
                </div>
                <div>
                  <p className="card-strong">Sagar Mahewar</p>
                  <p className="card-muted">Platform Owner</p>
                </div>
              </section>
              <div className="profile-actions">
                <div className="profile-action-item">
                  <button type="button" onClick={() => showFutureHint("settings")}>
                    <Settings size={15} />
                    Settings
                  </button>
                </div>
                <div className="profile-action-item">
                  <button type="button" onClick={() => showFutureHint("profile")}>
                    <CircleUser size={15} />
                    Profile
                  </button>
                </div>
              </div>
              {futureHintTarget && (
                <p className="future-hint-inline" role="status">
                  This feature is planned and will be available in a future release.
                </p>
              )}
              <p className="credit-line">
                Co-engineered with <strong>Microsoft Tools</strong> — a portfolio build by{" "}
                <strong>Sagar Mahewar</strong>.
              </p>
            </>
          )}
          <button
            className="collapse-button"
            onClick={() => setSidebarCollapsed((current) => !current)}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
            {!sidebarCollapsed && <span>Collapse sidebar</span>}
          </button>
        </div>
      </aside>

      <main className="main-shell">
        <header className="main-topbar">
          <button className="icon-button desktop-hidden" onClick={() => setSidebarOpen(true)} aria-label="Open menu">
            <Menu size={18} />
          </button>
          <div>
            <h1>Ask AI</h1>
            <p>Get accurate answers from your enterprise knowledge.</p>
          </div>
        </header>

        {navNotice && (
          <p className="status-line warning" role="status">
            {navNotice}
          </p>
        )}

        {(activeView === "ask-ai" || activeView === "answer-history") && (
          <>
            <section className="query-panel">
              <form onSubmit={onAsk} className="query-form">
                <textarea
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={(event) => void onQuestionKeyDown(event)}
                  placeholder="Attach or select document(s) first, then ask a question grounded in those sources..."
                  rows={4}
                />
                <div className="query-toolbar">
                  <label>
                    Focus mode
                    <select value={focusMode} onChange={(event) => setFocusMode(event.target.value as FocusMode)}>
                      <option value="balanced">Balanced</option>
                      <option value="precision">Precision</option>
                      <option value="broad">Broad search</option>
                    </select>
                  </label>
                  <button type="button" className="ghost-button" onClick={() => setActiveView("source-library")}>
                    <Paperclip size={15} />
                    Attach documents ({selectedDocumentIds.size})
                  </button>
                  <span className="kbd-hint">Ask: Ctrl/⌘ + Enter</span>
                  <button type="submit" className="primary-button" disabled={asking} aria-label="Submit question">
                    <Sparkles size={15} />
                    {asking ? "Asking..." : "Ask AI"}
                  </button>
                </div>
              </form>
            </section>

            <section className="chips-panel">
              <div className="chip-row">
                {INTEGRATIONS.map((integration) => (
                  <span key={integration.key} className={`integration-chip ${integration.status}`}>
                    <span className="chip-icon">{integration.icon}</span>
                    {integration.label}
                  </span>
                ))}
                {selectedDocumentIds.size > 0 && (
                  <span className="integration-chip connected">
                    <span className="chip-icon">
                      <Layers3 size={14} />
                    </span>
                    Scoped documents: {selectedDocumentIds.size}
                  </span>
                )}
                <button type="button" className="chip-action" onClick={() => setActiveView("source-library")}>
                  <SlidersHorizontal size={14} />
                  Manage Sources
                </button>
              </div>
              <div>
                <p className="panel-title">
                  Suggested Questions{selectedDocumentIds.size > 0 ? " for Selected Documents" : ""}
                </p>
                <div className="suggested-grid">
                  {suggestedQuestions.map((item) => (
                    <button key={item} type="button" className="suggested-card" onClick={() => void submitQuestion(item)}>
                      <MessageCircle size={15} />
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            </section>

            <section className="answer-layout">
              <div className="answer-column">
                <article className="answer-panel">
                  {!activeConversation && <p className="status-line">Ask a question to start conversation.</p>}
                  {qaError && (
                    <p className="status-line error" role="alert">
                      {qaError}
                    </p>
                  )}
                  {activeConversation && qaResponse && (
                    <>
                      <header className="message-header user">
                        <div className="avatar user-avatar">
                          <CircleUser size={17} />
                        </div>
                        <div>
                          <p className="message-title">You asked</p>
                          <p className="message-meta">
                            {new Date(activeConversation.askedAt).toLocaleString()} · {formatRelativeTime(activeConversation.askedAt)}
                          </p>
                        </div>
                      </header>
                      <p className="question-text">{activeConversation.question}</p>

                      <header className="message-header assistant">
                        <div className="avatar ai-avatar">
                          <Sparkles size={17} />
                        </div>
                        <div>
                          <p className="message-title">AI response</p>
                          <p className="message-meta">
                            Confidence:{" "}
                            <span className={`confidence-pill ${confidenceLabel === "n/a" ? "low" : confidenceLabel}`}>
                              {confidenceLabel === "n/a"
                                ? "n/a"
                                : `${confidenceLabel} (${Math.round((confidenceScore ?? 0) * 100)}%)`}
                            </span>
                          </p>
                        </div>
                      </header>

                      <div className="answer-body answer-markdown">
                        <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                          {normalizeAnswerForMarkdown(qaResponse.answer)}
                        </ReactMarkdown>
                        {qaResponse.insufficient_context && (
                          <p className="status-line warning">Insufficient context for a high-confidence grounded answer.</p>
                        )}
                      </div>

                      {keyPoints.length > 0 && (
                        <section className="subsection">
                          <p className="panel-title">Key points</p>
                          <ul>
                            {keyPoints.map((point) => (
                              <li key={point}>{point}</li>
                            ))}
                          </ul>
                        </section>
                      )}

                      <section className="subsection">
                        <p className="panel-title">Related policies and documents</p>
                        <div className="doc-tags">
                          {qaResponse.citations.length === 0 && <span className="tag muted">No linked documents</span>}
                          {Array.from(new Set(qaResponse.citations.map((citation) => citation.document_name))).map((name) => (
                            <span key={name} className="tag">
                              <FileText size={13} />
                              {name}
                            </span>
                          ))}
                        </div>
                      </section>

                      <div className="answer-actions">
                        <button type="button" onClick={() => void copyAnswerText()}>
                          <Copy size={15} />
                          Copy answer
                        </button>
                        <button
                          type="button"
                          className={feedbackByConversation[activeConversation.id] === "good" ? "selected" : ""}
                          onClick={() => markFeedback("good")}
                        >
                          <ThumbsUp size={15} />
                          Good answer
                        </button>
                        <button
                          type="button"
                          className={feedbackByConversation[activeConversation.id] === "not-useful" ? "selected" : ""}
                          onClick={() => markFeedback("not-useful")}
                        >
                          <ThumbsDown size={15} />
                          Not useful
                        </button>
                        <button
                          type="button"
                          className={bookmarkedConversations.has(activeConversation.id) ? "selected" : ""}
                          onClick={toggleBookmark}
                        >
                          <Bookmark size={15} />
                          Bookmark
                        </button>
                      </div>
                      {copyMessage && <p className="status-line">{copyMessage}</p>}
                    </>
                  )}
                </article>

                {activeConversation && followUpQuestions.length > 0 && (
                  <section className="panel follow-up-panel">
                    <h2>Follow-up Questions</h2>
                    <div className="follow-up-grid">
                      {followUpQuestions.map((item) => (
                        <button key={item} type="button" className="follow-up-card" onClick={() => void submitQuestion(item)}>
                          <MessageCircle size={15} />
                          {item}
                        </button>
                      ))}
                    </div>
                  </section>
                )}

                {qaResponse && (
                  <section className="panel">
                    <h2>Retrieved chunk viewer</h2>
                    {qaResponse.retrieved_chunks.length === 0 && <p className="status-line">No retrieved chunks for this answer.</p>}
                    {qaResponse.retrieved_chunks.length > 0 && (
                      <div className="chunk-list">
                        {qaResponse.retrieved_chunks.map((chunk) => {
                          const citation = citationByChunkId.get(chunk.chunk_id);
                          return (
                            <details key={chunk.chunk_id} className="chunk-card" id={`chunk-${chunk.chunk_id}`}>
                              <summary className="chunk-summary">
                                <div className="chunk-summary-main">
                                  <SourceTypeIcon sourceType={getSourceType(documentById.get(chunk.document_id)?.mime_type ?? "")} />
                                  <strong>{chunk.document_name}</strong>
                                </div>
                                <div className="chunk-summary-meta">
                                  <span>Page: {chunk.page_ref ?? citation?.page_ref ?? "n/a"}</span>
                                  <span>Retrieval score: {chunk.score?.toFixed(4) ?? "n/a"}</span>
                                </div>
                              </summary>
                              <div className="chunk-content">
                                <p>{chunk.text}</p>
                                {citation ? (
                                  <p className="chunk-citation-line">
                                    Cited in answer · Confidence {citation.confidence_score.toFixed(2)} · Citation score{" "}
                                    {citation.score?.toFixed(4) ?? "n/a"}
                                  </p>
                                ) : (
                                  <p className="chunk-citation-line">Retrieved for context (not directly cited in final answer)</p>
                                )}
                                <p className="chunk-metadata-label">Metadata</p>
                                <pre>{JSON.stringify(chunk.metadata, null, 2)}</pre>
                              </div>
                            </details>
                          );
                        })}
                      </div>
                    )}
                  </section>
                )}
              </div>

              <aside className="insights-column">
                <section className="panel metrics-panel">
                  <h2>Answer insights</h2>
                  {!activeConversation && <p className="status-line">Insights appear after a question is answered.</p>}
                  {activeConversation && qaResponse && (
                    <>
                      <div className="metric-grid">
                        <article className="metric-card">
                          <p>
                            <Clock3 size={18} className="metric-icon tone-knowledge" />
                            Response time
                          </p>
                          <strong>{activeConversation.responseMs} ms</strong>
                        </article>
                        <article className="metric-card">
                          <p>
                            <Layers3 size={18} className="metric-icon tone-ai" />
                            Sources used
                          </p>
                          <strong>{qaResponse.citations.length}</strong>
                        </article>
                        <article className="metric-card">
                          <p>
                            <ShieldCheck size={18} className="metric-icon tone-security" />
                            Confidence score
                          </p>
                          <strong>{confidenceScore === null ? "n/a" : `${Math.round(confidenceScore * 100)}%`}</strong>
                        </article>
                      </div>

                      <p className="status-line">Detailed sources are available in the Retrieved chunk viewer.</p>
                    </>
                  )}
                </section>

                <section className="panel">
                  <h2>Conversation history</h2>
                  {conversation.length === 0 && <p className="status-line">No questions asked yet.</p>}
                  <div className="history-list">
                    {[...conversation].reverse().map((entry) => (
                      <button
                        key={entry.id}
                        type="button"
                        className={`history-item ${activeConversation?.id === entry.id ? "active" : ""}`}
                        onClick={() => {
                          setActiveConversationId(entry.id);
                          setActiveView("ask-ai");
                        }}
                      >
                        <span>{entry.question}</span>
                        <small>
                          <Clock3 size={12} />
                          {new Date(entry.askedAt).toLocaleTimeString()}
                        </small>
                      </button>
                    ))}
                  </div>
                </section>
              </aside>
            </section>
          </>
        )}

        {activeView === "source-library" && (
          <>
            <section className="panel source-library-panel">
              <div className="panel-title-row">
                <h2>Source Library</h2>
                <button type="button" onClick={() => void refreshDocuments()} disabled={loadingDocuments}>
                  <RefreshCw size={15} />
                  Refresh
                </button>
              </div>
              <p className="source-library-intro">
                Curate trusted source documents to deliver grounded, citation-backed answers.
              </p>

              <form onSubmit={onUploadSubmit} className="upload-form">
                <div className="drop-zone" role="presentation" onDragOver={(event) => event.preventDefault()} onDrop={onDropFile}>
                  <label htmlFor="upload-file-input">
                    <CloudUpload size={16} />
                    PDF, DOCX, TXT
                  </label>
                  <input
                    id="upload-file-input"
                    type="file"
                    accept={SUPPORTED_TYPES}
                    onChange={onSelectFile}
                    disabled={uploading}
                  />
                  <p>{uploadFile ? `Selected: ${uploadFile.name}` : "Drag and drop or choose a file"}</p>
                </div>
                <button type="submit" className="primary-button" disabled={uploading}>
                  <CloudUpload size={15} />
                  {uploading ? "Uploading..." : "Upload document"}
                </button>
              </form>

              {uploadProgress !== null && (
                <p className="status-line" aria-live="polite">
                  Upload progress: {uploadProgress}%
                </p>
              )}
              {uploadError && (
                <p className="status-line error" role="alert">
                  {uploadError}
                </p>
              )}
            </section>

            <section className="panel">
              <div className="panel-title-row">
                <h2>Document management</h2>
                <p className="status-line">
                  Selected {selectedDocumentIds.size} of {documents.length} documents
                </p>
              </div>

              <div className="filter-row">
                <label>
                  <span className="filter-label">
                    <Users size={14} />
                    Department
                  </span>
                  <select value={departmentFilter} onChange={(event) => setDepartmentFilter(event.target.value)}>
                    <option value="all">All departments</option>
                  </select>
                </label>
                <label>
                  <span className="filter-label">
                    <CalendarDays size={14} />
                    Date range
                  </span>
                  <select value={dateRangeFilter} onChange={(event) => setDateRangeFilter(event.target.value as DateRange)}>
                    <option value="all">All time</option>
                    <option value="7d">Last 7 days</option>
                    <option value="30d">Last 30 days</option>
                    <option value="90d">Last 90 days</option>
                  </select>
                </label>
                <label>
                  <span className="filter-label">
                    <Library size={14} />
                    Knowledge source
                  </span>
                  <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value as KnowledgeSource)}>
                    <option value="all">All sources</option>
                    <option value="pdf">PDF</option>
                    <option value="docx">DOCX</option>
                    <option value="txt">TXT</option>
                  </select>
                </label>
                <button type="button" onClick={clearFilters}>
                  <SlidersHorizontal size={15} />
                  Clear filters
                </button>
              </div>

              <div className="document-tools">
                <div className="search-wrap">
                  <Search size={15} />
                  <input
                    type="search"
                    placeholder="Search by name, mime type, or ID"
                    value={documentQuery}
                    onChange={(event) => setDocumentQuery(event.target.value)}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedDocumentIds(new Set(filteredDocuments.map((doc) => doc.document_id)))}
                >
                  <Layers3 size={15} />
                  Select filtered
                </button>
                <button type="button" onClick={() => setSelectedDocumentIds(new Set())}>
                  <X size={15} />
                  Clear selection
                </button>
              </div>

              {documentsError && (
                <p className="status-line error" role="alert">
                  {documentsError}
                </p>
              )}

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Select</th>
                      <th>Name</th>
                      <th>Type</th>
                      <th>Size</th>
                      <th>Ingested</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredDocuments.length === 0 && (
                      <tr>
                        <td colSpan={5}>{loadingDocuments ? "Loading..." : "No documents found."}</td>
                      </tr>
                    )}
                    {filteredDocuments.map((document) => (
                      <tr key={document.document_id}>
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedDocumentIds.has(document.document_id)}
                            onChange={() => toggleDocumentSelection(document.document_id)}
                          />
                        </td>
                        <td>{document.document_name}</td>
                        <td>{getSourceType(document.mime_type)}</td>
                        <td>{formatBytes(document.byte_size)}</td>
                        <td>{new Date(document.ingested_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
