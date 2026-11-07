import { appConfig } from "./config";
import type { DocumentRecord, QAAskResponse, UploadResponse } from "./types";

type QAAskRequest = {
  query: string;
  top_k?: number;
  document_ids?: string[];
};

function buildErrorMessage(prefix: string, payload: unknown): string {
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string") {
      return `${prefix}: ${detail}`;
    }
  }
  return prefix;
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  const response = await fetch(`${appConfig.apiBaseUrl}/documents`);
  const payload = (await response.json()) as unknown;
  if (!response.ok) {
    throw new Error(buildErrorMessage("Failed to load documents", payload));
  }
  const documents = (payload as { documents?: DocumentRecord[] }).documents;
  return Array.isArray(documents) ? documents : [];
}

export async function askQuestion(request: QAAskRequest): Promise<QAAskResponse> {
  const response = await fetch(`${appConfig.apiBaseUrl}/qa/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request)
  });
  const payload = (await response.json()) as unknown;
  if (!response.ok) {
    throw new Error(buildErrorMessage("Question request failed", payload));
  }
  return payload as QAAskResponse;
}

export function uploadDocument(
  file: File,
  onProgress?: (percent: number) => void
): Promise<UploadResponse> {
  return new Promise<UploadResponse>((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", `${appConfig.apiBaseUrl}/documents/upload`);
    request.responseType = "json";

    request.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable && onProgress) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(Math.min(100, Math.max(0, percent)));
      }
    });

    request.addEventListener("load", () => {
      const payload = request.response as unknown;
      if (request.status >= 200 && request.status < 300) {
        resolve(payload as UploadResponse);
        return;
      }
      reject(new Error(buildErrorMessage("Upload failed", payload)));
    });

    request.addEventListener("error", () => {
      reject(new Error("Upload failed: network error"));
    });

    const formData = new FormData();
    formData.append("file", file);
    request.send(formData);
  });
}
