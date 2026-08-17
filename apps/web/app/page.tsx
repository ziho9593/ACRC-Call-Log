"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { deleteCall, listCalls, uploadCall, validateAudioFile } from "@/lib/api";
import type { CallSummary } from "@/types/call";

const statusLabels: Record<CallSummary["status"], string> = {
  UPLOADED: "업로드됨",
  PROCESSING: "처리 중",
  COMPLETED: "완료",
  FAILED: "실패"
};

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)}KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

export default function HomePage() {
  const [calls, setCalls] = useState<CallSummary[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingCallId, setDeletingCallId] = useState<string | null>(null);
  const [trackedCallId, setTrackedCallId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshCalls = useCallback(async () => {
    const items = await listCalls();
    setCalls(items);
    return items;
  }, []);

  useEffect(() => {
    refreshCalls().catch(() => setError("최근 처리 목록을 불러오지 못했습니다."));
  }, [refreshCalls]);

  useEffect(() => {
    if (!trackedCallId) {
      return;
    }

    const trackedCall = calls.find((call) => call.id === trackedCallId);
    if (trackedCall?.status === "COMPLETED") {
      setMessage("분석이 완료되었습니다.");
      setTrackedCallId(null);
    } else if (trackedCall?.status === "FAILED") {
      setMessage(null);
      setError(trackedCall.errorMessage ?? "분석 처리에 실패했습니다.");
      setTrackedCallId(null);
    }
  }, [calls, trackedCallId]);

  useEffect(() => {
    if (!calls.some((call) => call.status === "UPLOADED" || call.status === "PROCESSING")) {
      return;
    }

    const timer = window.setTimeout(async () => {
      try {
        await refreshCalls();
      } catch {
        setError("처리 상태를 갱신하지 못했습니다.");
      }
    }, 2000);

    return () => window.clearTimeout(timer);
  }, [calls, refreshCalls]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    const validationError = validateAudioFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsUploading(true);
    try {
      const uploadedCall = await uploadCall(file as File);
      setMessage("업로드가 완료되었습니다. 분석 상태를 확인하고 있습니다.");
      setTrackedCallId(uploadedCall.id);
      setFile(null);
      await refreshCalls();
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "업로드 중 오류가 발생했습니다.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(call: CallSummary) {
    if (!window.confirm(`'${call.originalFilename}' 기록과 녹취 파일을 삭제할까요?`)) {
      return;
    }

    setDeletingCallId(call.id);
    setError(null);
    setMessage(null);
    try {
      await deleteCall(call.id);
      setCalls((current) => current.filter((item) => item.id !== call.id));
      if (trackedCallId === call.id) {
        setTrackedCallId(null);
      }
      setMessage("통화 기록을 삭제했습니다.");
    } catch (deleteError) {
      setError(
        deleteError instanceof Error ? deleteError.message : "통화 기록을 삭제하지 못했습니다."
      );
    } finally {
      setDeletingCallId(null);
    }
  }

  return (
    <main className="page">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">ACRC-Call-Log</div>
        </div>
      </header>

      <div className="content">
        <section className="intro">
          <div className="headline">
            <h1>통화 녹취 분석 PoC</h1>
            <p>
              녹취 파일을 업로드하면 로컬 모델의 전사와 상담 분석 결과를 확인할 수 있습니다.
              전사문에는 타임스탬프가 포함되며, 상세 화면에서 특정 구간을 눌러 오디오 위치를 이동할
              수 있습니다.
            </p>
          </div>

          <form className="panel upload-panel" onSubmit={handleSubmit}>
            <label className="upload-label" htmlFor="audio-file">
              녹취 파일 업로드
            </label>
            <input
              id="audio-file"
              className="file-input"
              type="file"
              accept=".mp3,.wav,.m4a,.mp4,audio/*,video/mp4"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
            <p className="hint">지원 형식: mp3, wav, m4a, mp4 / 최대 100MB</p>
            <button className="primary-button" type="submit" disabled={isUploading}>
              {isUploading ? "업로드 중" : "업로드 및 분석 시작"}
            </button>
            {message ? <div className="message info">{message}</div> : null}
            {error ? <div className="message error">{error}</div> : null}
          </form>
        </section>

        <h2 className="section-title">최근 처리한 통화 목록</h2>
        <section className="panel call-list" aria-label="최근 처리한 통화 목록">
          {calls.length === 0 ? (
            <div className="empty">아직 업로드된 통화가 없습니다.</div>
          ) : (
            calls.map((call) => (
              <article className="call-row" key={call.id}>
                <Link className="call-row-link" href={`/calls/${call.id}`}>
                  <div>
                    <div className="call-name">{call.originalFilename}</div>
                    <div className="call-meta">
                      {formatBytes(call.fileSizeBytes)} ·{" "}
                      {new Date(call.createdAt).toLocaleString("ko-KR")}
                    </div>
                  </div>
                  <span className={`status ${call.status}`}>{statusLabels[call.status]}</span>
                  <div className="call-meta">{call.oneLineSummary ?? "분석 결과 대기 중"}</div>
                </Link>
                <button
                  className="delete-button"
                  type="button"
                  aria-label={`${call.originalFilename} 삭제`}
                  disabled={deletingCallId === call.id}
                  onClick={() => handleDelete(call)}
                >
                  {deletingCallId === call.id ? "삭제 중" : "삭제"}
                </button>
              </article>
            ))
          )}
        </section>
      </div>
    </main>
  );
}

