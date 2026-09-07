import { useState, type FormEvent } from "react";
import { HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

export function ClarificationPrompt({
  question,
  onSubmit,
  isSubmitting,
}: {
  question: string;
  onSubmit: (answer: string) => void;
  isSubmitting: boolean;
}) {
  const [answer, setAnswer] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (answer.trim()) onSubmit(answer.trim());
  };

  return (
    <Card className="border-signal/40 bg-signal-light/40 p-4">
      <div className="flex gap-3">
        <HelpCircle className="mt-0.5 h-5 w-5 shrink-0 text-signal-dark" />
        <div className="flex-1">
          <p className="text-sm font-medium text-ink">Senselytics needs a bit more detail</p>
          <p className="mt-1 text-sm text-slate-600">{question}</p>
          <form onSubmit={handleSubmit} className="mt-3 flex gap-2">
            <Input
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer"
              className="flex-1"
              autoFocus
            />
            <Button type="submit" isLoading={isSubmitting} disabled={!answer.trim()}>
              Send
            </Button>
          </form>
        </div>
      </div>
    </Card>
  );
}
