import { useState } from "react";

export default function VoiceRecorder({
  onTranscript,
}: {
  onTranscript: (text: string) => void;
}) {
  const [listening, setListening] = useState(false);

  const startRecording = () => {
    const SpeechRecognition =
      (window as any).webkitSpeechRecognition ||
      (window as any).SpeechRecognition;

    console.log("Voice button clicked");

    if (!SpeechRecognition) {
      alert("Speech Recognition not supported");
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      console.log("Recording started");
      setListening(true);
    };

    recognition.onend = () => {
      console.log("Recording ended");
      setListening(false);
    };

    recognition.onresult = (event: any) => {
      let transcript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }

      console.log("TRANSCRIPT:", transcript);

      if (transcript.trim()) {
        onTranscript(transcript.trim());
      }
    };

    recognition.onerror = (event: any) => {
      console.log("Speech Error:", event.error);
    };

    recognition.onnomatch = () => {
      console.log("No speech match");
    };

    recognition.start();
  };

  return (
    <button
      onClick={startRecording}
      className="px-3 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 text-white text-xs font-medium"
    >
      {listening ? "🎙 Recording..." : "🎤 Dictate Report"}
    </button>
  );
}