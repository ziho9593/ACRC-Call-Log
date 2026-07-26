export type CallStatus = "UPLOADED" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface CallSummary {
  id: string;
  originalFilename: string;
  mimeType: string;
  fileSizeBytes: number;
  status: CallStatus;
  errorMessage: string | null;
  durationMs: number | null;
  oneLineSummary: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Utterance {
  id: number;
  sequence: number;
  speaker: string;
  startMs: number;
  endMs: number;
  text: string;
}

export interface CallSection {
  id: number;
  sequence: number;
  title: string;
  startMs: number;
  endMs: number;
  summary: string;
  keywords: string[];
}

export interface CallDetail extends CallSummary {
  detailedSummary: string | null;
  keywords: string[];
  utterances: Utterance[];
  sections: CallSection[];
}

export interface CallStatusResponse {
  id: string;
  status: CallStatus;
  errorMessage: string | null;
  updatedAt: string;
}

