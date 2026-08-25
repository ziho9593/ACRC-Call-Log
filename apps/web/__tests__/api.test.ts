import { describe, expect, it, vi } from "vitest";
import { deleteCall, validateAudioFile } from "@/lib/api";

describe("validateAudioFile", () => {
  it("업로드 파일이 없으면 오류를 반환한다", () => {
    expect(validateAudioFile(null)).toBe("업로드할 녹취 파일을 선택해 주세요.");
  });

  it("지원하지 않는 확장자를 거부한다", () => {
    const file = new File(["hello"], "memo.txt", { type: "text/plain" });
    expect(validateAudioFile(file)).toBe("mp3, wav, m4a, mp4 파일만 업로드할 수 있습니다.");
  });

  it("지원하는 음성 파일은 통과한다", () => {
    const file = new File(["audio"], "call.mp3", { type: "audio/mpeg" });
    expect(validateAudioFile(file)).toBeNull();
  });

  it("통화 삭제 요청을 보낸다", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, {
        status: 204
      })
    );

    await deleteCall("call-1");

    expect(fetchMock).toHaveBeenCalledWith("/api/v1/calls/call-1", {
      method: "DELETE"
    });
    fetchMock.mockRestore();
  });
});

