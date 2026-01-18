MONEYBIRD

## Inspiration

As university students, we constantly see friends and classmates struggling with money in silence. Tuition, rent, credit cards, and job uncertainty create stress that feels personal and isolating. We wanted to build something we would actually use ourselves: a place to talk through financial stress without judgment, pressure, or needing to already “know what to do.”

## What it does

MoneyBird is a financial support companion designed for moments when money feels overwhelming. Users can talk openly about their situation, and MoneyBird listens first, understands emotional context, and then helps break financial problems into manageable, realistic next steps. It focuses on clarity and calm rather than rigid advice.

## How we built it

We built MoneyBird as a full-stack web application. The frontend is built with Next.js and Tailwind CSS for a clean, responsive interface. The backend uses FastAPI and LangGraph to orchestrate multiple AI agents, including an emotional intake agent, a financial reasoning agent, and a synthesizer that adjusts responses based on user stress levels. Supabase is used for session persistence, conversation history, and agent logging.

## Challenges we ran into

One of our biggest challenges was managing complexity without overwhelming the user. Financial guidance is not just about numbers; emotional state matters. We also faced technical challenges coordinating multiple agents, handling state across conversations, and resolving real-world issues like dependency conflicts, version mismatches, and merge conflicts under time pressure.

## Accomplishments that we're proud of

We’re proud of building a system that treats financial stress as both an emotional and practical problem. We successfully implemented a multi-agent architecture with clear state management and logging, and we designed a user experience that feels supportive rather than intimidating. Most importantly, we built something we genuinely believe could help people.

## What we learned

We learned that good AI systems are as much about orchestration and safety as they are about model output. Separating concerns between emotional understanding, financial reasoning, and final response generation made the system more controllable and humane. We also gained hands-on experience with full-stack integration, agent coordination, and collaborative development under real constraints.

## What's next for MoneyBird

Next, we want to improve personalization, integrate user authentication, and expand long-term progress tracking. We also plan to refine safety features, improve financial education prompts, and explore partnerships that could make MoneyBird accessible to more students and young professionals.
