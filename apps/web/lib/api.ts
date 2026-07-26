import type { CallDetail, CallStatusResponse, CallSummary } from "@/types/call";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const MAX_UPLOAD_BYTES = 100 * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".mp3", ".wav", ".m4a", ".mp4"];

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    let message = "요청 처리 중 오류가 발생했습니다.";
    try {
      const body = (await response.json()) as { detail?: string };
      message = body.detail ?? message;
    } catch {
      // Keep the friendly fallback message.
    }
    throw new ApiError(message, response.status);
  }
  return (await response.json()) as T;
}

export function validateAudioFile(file: File | null): string | null {
  if (!file) {
    return "업로드할 녹취 파일을 선택해 주세요.";
  }
  const lowerName = file.name.toLowerCase();
  if (!ALLOWED_EXTENSIONS.some((extension) => lowerName.endsWith(extension))) {
    return "mp3, wav, m4a, mp4 파일만 업로드할 수 있습니다.";
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return "파일 크기는 100MB를 초과할 수 없습니다.";
  }
  return null;
}

export async function uploadCall(file: File): Promise<CallSummary> {
  const formData = new FormData();
  formData.append("file", file);
  return request<CallSummary>("/api/v1/calls", {
    method: "POST",
    body: formData
  });
}

export async function listCalls(): Promise<CallSummary[]> {
  const result = await request<{ items: CallSummary[] }>("/api/v1/calls");
  return result.items;
}

export async function getCall(callId: string): Promise<CallDetail> {
  return request<CallDetail>(`/api/v1/calls/${callId}`);
}

export async function getCallStatus(callId: string): Promise<CallStatusResponse> {
  return request<CallStatusResponse>(`/api/v1/calls/${callId}/status`);
}

export function getAudioUrl(callId: string): string {
  return `${API_BASE_URL}/api/v1/calls/${callId}/audio`;
}

