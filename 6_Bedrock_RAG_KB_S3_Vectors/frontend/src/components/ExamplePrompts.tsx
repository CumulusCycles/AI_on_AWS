const EXAMPLES = [
  'What products does AI Agent Insure offer?',
  'What does Agentic AI Liability Insurance cover?',
  'How does the claims process work?',
  'What is the coverage limit for AI Infrastructure Operations Protection?',
  'Does AI Agent Insure cover regulatory fines?',
  'What incidents are covered under Autonomous Systems & Robotics Coverage?',
];

interface ExamplePromptsProps {
  onSelect: (prompt: string) => void;
}

export default function ExamplePrompts({ onSelect }: ExamplePromptsProps) {
  return (
    <div className="mt-6">
      <p className="text-xs uppercase tracking-widest text-aws-muted font-semibold mb-3">
        Try asking…
      </p>
      <div className="flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => onSelect(ex)}
            className="text-sm bg-aws-card border border-aws-border text-aws-text rounded-md px-3 py-1.5 hover:border-aws-orange hover:text-aws-orange transition-colors text-left"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
