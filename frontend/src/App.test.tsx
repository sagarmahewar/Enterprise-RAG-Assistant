import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { App } from "./App";
import { askQuestion, listDocuments, uploadDocument } from "./api";

vi.mock("./api", () => ({
  listDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  askQuestion: vi.fn()
}));

const mockedListDocuments = vi.mocked(listDocuments);
const mockedUploadDocument = vi.mocked(uploadDocument);
const mockedAskQuestion = vi.mocked(askQuestion);
const QUERY_PLACEHOLDER = "Attach or select document(s) first, then ask a question grounded in those sources...";

describe("App", () => {
  beforeEach(() => {
    mockedListDocuments.mockReset();
    mockedListDocuments.mockResolvedValue([
      {
        document_id: "doc-1",
        document_name: "policy.txt",
        mime_type: "text/plain",
        byte_size: 1024,
        parser_name: "text-parser",
        ingested_at: "2026-11-06T15:00:00Z"
      }
    ]);
    mockedUploadDocument.mockReset();
    mockedAskQuestion.mockReset();
  });

  it("renders heading and loads documents", async () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Ask AI" })).toBeTruthy();
    await waitFor(() => expect(mockedListDocuments).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Source Library" }));
    expect(screen.getByText("policy.txt")).toBeTruthy();
  });

  it("handles upload flow and progress", async () => {
    mockedUploadDocument.mockImplementation(async (_file, onProgress) => {
      onProgress?.(40);
      onProgress?.(100);
      return {
        document_id: "doc-2",
        document_name: "new.txt",
        mime_type: "text/plain",
        size_bytes: 512,
        chunk_count: 1,
        parser_name: "text-parser"
      };
    });
    render(<App />);
    await waitFor(() => expect(mockedListDocuments).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "Source Library" }));
    const fileInput = screen.getByLabelText("PDF, DOCX, TXT") as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [new File(["hello"], "new.txt")] } });
    fireEvent.click(screen.getByText("Upload document"));

    await waitFor(() => expect(mockedUploadDocument).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockedListDocuments.mock.calls.length).toBeGreaterThanOrEqual(2));
  });

  it("renders QA answer, citations, and retrieved chunks", async () => {
    mockedAskQuestion.mockResolvedValue({
      query: "What is retention policy?",
      answer: "Records are retained for seven years.",
      insufficient_context: false,
      citation_confidence_threshold: 0.35,
      citations: [
        {
          document_id: "doc-1",
          document_name: "policy.txt",
          chunk_id: "chunk-1",
          page_ref: "1",
          score: 0.88,
          confidence_score: 0.88,
          confidence_label: "high",
          meets_confidence_threshold: true
        }
      ],
      retrieved_chunks: [
        {
          chunk_id: "chunk-1",
          document_id: "doc-1",
          document_name: "policy.txt",
          page_ref: "1",
          text: "Retention policy requires seven years.",
          score: 0.88,
          metadata: { fused_score: "0.88" }
        }
      ],
      total_chunks: 1
    });

    render(<App />);
    await waitFor(() => expect(mockedListDocuments).toHaveBeenCalled());

    fireEvent.change(screen.getByPlaceholderText(QUERY_PLACEHOLDER), {
      target: { value: "What is retention policy?" }
    });
    fireEvent.click(screen.getByLabelText("Submit question"));

    await waitFor(() => expect(mockedAskQuestion).toHaveBeenCalledTimes(1));
    expect(screen.getAllByText("Records are retained for seven years.").length).toBeGreaterThan(0);
    expect(screen.getByText(/high \(88%\)/)).toBeTruthy();
    expect(screen.getAllByText("Retention policy requires seven years.").length).toBeGreaterThan(0);
  });

  it("shows key error states", async () => {
    mockedListDocuments.mockRejectedValueOnce(new Error("Failed to load documents"));
    mockedUploadDocument.mockRejectedValue(new Error("Upload failed"));
    mockedAskQuestion.mockRejectedValue(new Error("Question request failed"));

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Source Library" }));
    await waitFor(() => {
      expect(screen.getByText("Failed to load documents")).toBeTruthy();
    });

    const fileInput = screen.getByLabelText("PDF, DOCX, TXT") as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [new File(["bad"], "bad.txt")] } });
    fireEvent.click(screen.getByText("Upload document"));
    await waitFor(() => expect(screen.getByText("Upload failed")).toBeTruthy());

    fireEvent.click(screen.getByRole("button", { name: "Ask AI" }));
    fireEvent.change(screen.getByPlaceholderText(QUERY_PLACEHOLDER), {
      target: { value: "Any policy?" }
    });
    fireEvent.click(screen.getByLabelText("Submit question"));
    await waitFor(() => expect(screen.getByText("Question request failed")).toBeTruthy());
  });
});
