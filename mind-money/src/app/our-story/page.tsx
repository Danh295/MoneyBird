'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { MessageSquare, LayoutDashboard, ArrowLeft } from 'lucide-react';
import Image from 'next/image';

export default function OurStoryPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[var(--background)] flex flex-col">
      {/* Header/Navbar */}
      <div className="bg-white border-b border-[var(--border)] px-8 py-6 shadow-sm">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--neutral)] transition-colors"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-[var(--text-primary)]">Our Story</h1>
              <p className="text-[var(--text-secondary)] text-sm">Meet the team behind MoneyBird</p>
            </div>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 bg-[var(--neutral)] text-[var(--text-primary)] hover:bg-[var(--neutral-dark)]"
            >
              <MessageSquare size={16} /> Chat
            </button>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] text-white hover:shadow-md"
            >
              <LayoutDashboard size={16} /> Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          
          {/* Team Photo Section */}
          <div className="bg-white rounded-2xl border border-[var(--border)] shadow-lg p-8 mb-8">
            <div className="flex flex-col items-center">
              {/* Team Photo */}
              <div className="w-full max-w-2xl aspect-video relative rounded-xl overflow-hidden mb-6">
                <Image
                  src="/images/team.png"
                  alt="Our Team"
                  fill
                  className="object-cover"
                  priority
                />
              </div>
              
              {/* Team Name */}
              <h2 className="text-3xl font-bold text-[var(--text-primary)] mb-2 text-center bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] bg-clip-text text-transparent">
                [Yellow MoneyBird]
              </h2>
              
              <p className="text-sm text-[var(--text-secondary)] text-center">
                UofTHacks 13 • January 2026
              </p>
            </div>
          </div>

          {/* Story Section */}
          <div className="bg-white rounded-2xl border border-[var(--border)] shadow-lg p-8">
            <h3 className="text-xl font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
              <span className="text-2xl"></span>
              About Our Team
            </h3>
            
            <div className="prose prose-slate max-w-none">
              <p className="text-[var(--text-primary)] leading-relaxed mb-4">
                關於我們（詩）

我們成立於二〇二六年。
不是因為世界需要更多工具，
而是因為我們自己，
曾經站在生活裡，不知道該往哪裡飛。

我們的身高不一樣——
一七五公分，
一七〇公分，
一六六點五公分，
一五七點二公分。
但站在現實面前，
沒有人真的比較高。

我們之中，
有人從中國來，
有人從印尼來，
也有人出生在加拿大，
卻一樣在華人家庭的期待裡長大。
我們在多倫多、在萬錦市，
學會如何在語言之間切換，
在文化之間生存，
在夢想與責任之間保持平衡。
              </p>
              
              <p className="text-[var(--text-primary)] leading-relaxed mb-4">
                我們知道什麼叫做沒有退路。
知道存款數字不只是數字，
而是失眠的夜晚，
是不敢打開銀行 App 的早晨，
是對未來既期待、又害怕的矛盾。

沒有人教過我們，
如何同時照顧情緒與財務。
世界只要求你撐住、算清楚、別犯錯。
卻很少有人問：
你，還好嗎？

所以我們開始了這個專案。
不是為了完美，
而是為了誠實。
不是為了控制，
而是為了給人一雙能夠保持平衡的翅膀。

我們相信科技可以溫柔，
資料可以被尊重，
錯誤可以被承接，
而安全感，
是所有選擇之前最重要的前提。

我們來自不同的起點，
卻走向同一個方向——
讓人們在混亂中站得穩，
在壓力中不再孤單，
在準備好之前，
不必急著飛。
              </p>
              
              <div className="mt-6 p-4 bg-[var(--secondary-light)] rounded-lg border border-[var(--border)]">
                <p className="text-sm text-[var(--text-secondary)] italic text-center">
                  "We were founded in 2026. Not because the world needs more tools, but because we ourselves once stood in the midst of life, unsure of where to fly. We are all different heights—175 cm, 170 cm, 166.5 cm, 157.2 cm. But in reality, no one is truly taller. Some of us come from China, some from Indonesia, and some were born in Canada, yet all grew up under the same expectations of Chinese families. In Toronto and Markham, we learned how to switch between languages, survive across cultures, and maintain a balance between dreams and responsibilities.
<br></br>
We know what it means to have no way out. We know that bank account numbers are not just numbers, but represent sleepless nights, mornings too afraid to open the banking app, and the contradictory mix of anticipation and fear for the future. No one taught us how to manage our emotions and finances simultaneously. The world only demands that you hold on, calculate carefully, and avoid mistakes. Few ask: Are you okay? So we started this project. Not for perfection, but for honesty. It's not about control, but about giving people wings to maintain their balance. We believe technology can be gentle, data can be respected, mistakes can be accepted, and a sense of security is the most important prerequisite before any choice. We come from different starting points, but we are heading in the same direction—to help people stand firm in chaos, to no longer feel alone under pressure, and to not rush to fly before they are ready."
                </p>
              </div>
            </div>
          </div>

          {/* Back to Chat CTA */}
          <div className="mt-8 text-center">
            <button
              onClick={() => router.push('/')}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] text-white rounded-xl font-semibold hover:shadow-lg transition-all"
            >
              <MessageSquare size={18} />
              Start Chatting with MoneyBird
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
