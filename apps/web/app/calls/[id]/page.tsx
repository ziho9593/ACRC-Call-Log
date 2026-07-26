"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { getAudioUrl, getCall, getCallStatus } from "@/lib/api";
import type { CallDetail } from "@/types/call";

const statusLabels: Record<CallDetail["status"], string> = {
  UPLOADED: "업로드됨",
  PROCESSING: "처리 중",
  COMPLETED: "완료",
  FAILED: "실패"
};

function formatTime(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minute = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const second = (seconds % 60).toString().padStart(2, "0");
  return `${minute}:${second}`;
}

export default function CallDetailPage() {
  const params = useParams<{ id: string }>();
  const callId = params.id;
  const audioRef = useRef<HTMLAudioElement>(null);
  const [call, setCall] = useState<CallDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshDetail = useCallback(async () => {
    const detail = await getCall(callId);
    setCall(detail);
  }, [callId]);

  useEffect(() => {
    refreshDetail().catch(() => setError("통화 분석 정보를 불러오지 못했습니다."));
  }, [refreshDetail]);

  useEffect(() => {
    if (!call || call.status === "COMPLETED" || call.status === "FAILED") {
      return;
    }
    const timer = window.setInterval(async () => {
      try {
        const status = await getCallStatus(callId);
        setCall((current) => (current ? { ...current, ...status } : current));
        if (status.status === "COMPLETED" || status.status === "FAILED") {
          await refreshDetail();
        }
      } catch {
        setError("처리 상태를 갱신하지 못했습니다.");
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [call, callId, refreshDetail]);

  function seekTo(startMs: number) {
    if (!audioRef.current) {
      return;
    }
    audioRef.current.currentTime = startMs / 1000;
    audioRef.current.play().catch(() => undefined);
  }

  return (
    <main className="page">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">ACRC-Call-Log</div>
          <Link className="nav-link" href="/">
            목록으로
          </Link>
        </div>
      </header>

      <div className="content">
        {error ? <div className="message error">{error}</div> : null}
        {!call ? (
          <div className="panel empty">분석 정보를 불러오는 중입니다.</div>
        ) : (
          <div className="detail-grid">
            <aside className="panel side-panel">
              <div className="summary-block">
                <h2>{call.originalFilename}</h2>
                <span className={`status ${call.status}`}>{statusLabels[call.status]}</span>
                {call.errorMessage ? <div className="message error">{call.errorMessage}</div> : null}
              </div>

              <div className="summary-block">
                <h3>오디오 재생</h3>
                <audio ref={audioRef} className="audio" controls src={getAudioUrl(call.id)} />
              </div>

              <div className="summary-block">
                <h3>주요 키워드</h3>
                {call.keywords.length > 0 ? (
                  <ul className="keywords">
                    {call.keywords.map((keyword) => (
                      <li className="keyword" key={keyword}>
                        {keyword}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>분석 완료 후 표시됩니다.</p>
                )}
              </div>
            </aside>

            <section className="panel main-panel">
              <div className="summary-block">
                <h2>전체 요약</h2>
                <p>{call.oneLineSummary ?? "분석 결과를 기다리는 중입니다."}</p>
              </div>

              <div className="summary-block">
                <h3>상세 요약</h3>
                <p>{call.detailedSummary ?? "분석 완료 후 표시됩니다."}</p>
              </div>

              <div className="summary-block">
                <h3>구간별 핵심 내용</h3>
                <div className="section-list">
                  {call.sections.map((section) => (
                    <button
                      className="section-item"
                      key={section.id}
                      type="button"
                      onClick={() => seekTo(section.startMs)}
                    >
                      <span className="time">
                        {formatTime(section.startMs)} - {formatTime(section.endMs)}
                      </span>
                      <span className="speaker">{section.title}</span>
                      <p>{section.summary}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="summary-block">
                <h3>전체 전사문</h3>
                <div className="utterance-list">
                  {call.utterances.map((utterance) => (
                    <button
                      className="utterance-button"
                      key={utterance.id}
                      type="button"
                      onClick={() => seekTo(utterance.startMs)}
                    >
                      <span className="time">
                        {formatTime(utterance.startMs)} - {formatTime(utterance.endMs)}
                      </span>
                      <span className="speaker">{utterance.speaker}</span>
                      <p>{utterance.text}</p>
                    </button>
                  ))}
                </div>
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
