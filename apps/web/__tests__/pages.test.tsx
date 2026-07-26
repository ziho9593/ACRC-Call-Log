import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import CallDetailPage from "@/app/calls/[id]/page";
import HomePage from "@/app/page";

const apiMock = vi.hoisted(() => ({
  getAudioUrl: vi.fn(() => "http://localhost:8000/api/v1/calls/call-1/audio"),
  getCall: vi.fn(),
  getCallStatus: vi.fn(),
  listCalls: vi.fn(),
  uploadCall: vi.fn(),
  validateAudioFile: vi.fn((file: File | null) => (file ? null : "업로드할 녹취 파일을 선택해 주세요."))
}));

vi.mock("@/lib/api", () => apiMock);
vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "call-1" })
}));

describe("pages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("처리 상태별 UI를 표시한다", async () => {
    apiMock.listCalls.mockResolvedValue([
      {
        id: "1",
        originalFilename: "uploaded.mp3",
        mimeType: "audio/mpeg",
        fileSizeBytes: 1000,
        status: "UPLOADED",
        errorMessage: null,
        durationMs: null,
        oneLineSummary: null,
        createdAt: "2026-07-26T04:30:00Z",
        updatedAt: "2026-07-26T04:30:00Z"
      },
      {
        id: "2",
        originalFilename: "done.mp3",
        mimeType: "audio/mpeg",
        fileSizeBytes: 1000,
        status: "COMPLETED",
        errorMessage: null,
        durationMs: 64000,
        oneLineSummary: "민원 처리 상태 확인",
        createdAt: "2026-07-26T04:31:00Z",
        updatedAt: "2026-07-26T04:31:00Z"
      },
      {
        id: "3",
        originalFilename: "failed.mp3",
        mimeType: "audio/mpeg",
        fileSizeBytes: 1000,
        status: "FAILED",
        errorMessage: "오류",
        durationMs: null,
        oneLineSummary: null,
        createdAt: "2026-07-26T04:32:00Z",
        updatedAt: "2026-07-26T04:32:00Z"
      }
    ]);
    render(<HomePage />);
    expect(await screen.findByText("업로드됨")).toBeInTheDocument();
    expect(screen.getByText("완료")).toBeInTheDocument();
    expect(screen.getByText("실패")).toBeInTheDocument();
  });

  it("완료된 분석 결과를 렌더링한다", async () => {
    apiMock.getCall.mockResolvedValue({
      id: "call-1",
      originalFilename: "sample.mp3",
      mimeType: "audio/mpeg",
      fileSizeBytes: 1000,
      status: "COMPLETED",
      errorMessage: null,
      durationMs: 64000,
      oneLineSummary: "민원 처리 상태 지연 문의",
      detailedSummary: "담당 부서 배정은 완료되었고 검토가 지연된 상태입니다.",
      keywords: ["민원 접수"],
      createdAt: "2026-07-26T04:30:00Z",
      updatedAt: "2026-07-26T04:31:00Z",
      utterances: [
        {
          id: 1,
          sequence: 1,
          speaker: "상담원",
          startMs: 0,
          endMs: 5000,
          text: "안녕하세요."
        }
      ],
      sections: [
        {
          id: 1,
          sequence: 1,
          title: "문의 접수",
          startMs: 0,
          endMs: 5000,
          summary: "고객이 처리 상태를 문의했습니다.",
          keywords: ["처리 상태"]
        }
      ]
    });
    render(<CallDetailPage />);
    expect(await screen.findByText("민원 처리 상태 지연 문의")).toBeInTheDocument();
    expect(screen.getByText("민원 접수")).toBeInTheDocument();
    expect(screen.getByText("안녕하세요.")).toBeInTheDocument();
  });

  it("API 오류 상태를 표시한다", async () => {
    apiMock.listCalls.mockRejectedValue(new Error("목록 오류"));
    render(<HomePage />);
    await waitFor(() => {
      expect(screen.getByText("최근 처리 목록을 불러오지 못했습니다.")).toBeInTheDocument();
    });

    const submit = screen.getByRole("button", { name: "업로드 및 분석 시작" });
    await userEvent.click(submit);
    expect(screen.getByText("업로드할 녹취 파일을 선택해 주세요.")).toBeInTheDocument();
  });
});
