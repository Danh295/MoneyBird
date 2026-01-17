import MindMoneyChat from '@/components/MindMoneyChat';

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-100 flex flex-col">
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        {/* ... Keep your existing header ... */}
      </header>

      {/* The container for the chat */}
      <div className="flex-1 max-w-5xl w-full mx-auto p-4 md:p-6">
        <MindMoneyChat />
      </div>
    </main>
  );
}