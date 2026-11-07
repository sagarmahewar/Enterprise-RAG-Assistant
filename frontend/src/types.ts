export type DocumentRecord = {
  document_id: string;
  document_name: string;
  mime_type: string;
  byte_size: number;
  parser_name: string;
  ingested_at: string;
};

export type CitationRecord = {
  document_id: string;
  document_name: string;
  chunk_id: string;
  page_ref: string | null;
  score: number | null;
  confidence_score: number;
  confidence_label: "low" | "medium" | "high";
  meets_confidence_threshold: boolean;
};

export type RetrievedChunkRecord = {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_ref: string | null;
  text: string;
  score: number | null;
  metadata: Record<string, string>;
};

export type QAAskResponse = {
  query: string;
  answer: string;
  insufficient_context: boolean;
  citation_confidence_threshold: number;
  citations: CitationRecord[];
  retrieved_chunks: RetrievedChunkRecord[];
  total_chunks: number;
};

export type UploadResponse = {
  document_id: string;
  document_name: string;
  mime_type: string;
  size_bytes: number;
  chunk_count: number;
  parser_name: string;
};
