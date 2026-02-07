import { Link } from "react-router-dom";
import { useUser, SignOutButton } from "@clerk/clerk-react";

function HeroPage() {
  const { isSignedIn, user } = useUser();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-red-950 to-gray-900 text-white">
      {/* Navigation Bar */}
      <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
        <div className="text-2xl font-bold text-red-400">FinNet</div>
        <div className="flex items-center space-x-4">
          {isSignedIn ?
            <>
              <Link
                to="/playground"
                className="px-4 py-2 text-gray-300 hover:text-white transition"
              >
                Playground
              </Link>
              <div className="flex items-center space-x-3">
                <span className="text-gray-300 text-sm">
                  {user?.fullName || user?.primaryEmailAddress?.emailAddress}
                </span>
                <SignOutButton>
                  <button className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition">
                    Sign Out
                  </button>
                </SignOutButton>
              </div>
            </>
          : <>
              <Link
                to="/login"
                className="px-4 py-2 text-gray-300 hover:text-white transition"
              >
                Login
              </Link>
              <Link
                to="/signup"
                className="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition"
              >
                Sign Up
              </Link>
            </>
          }
        </div>
      </nav>

      {/* Hero Section */}
      <div className="container mx-auto px-6 py-20">
        <div className="max-w-4xl mx-auto text-center">
          {/* Main Heading */}
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Network-Based <span className="text-red-400">Game-Theoretic</span>{" "}
            Modeling of Financial Infrastructure
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-gray-300 mb-8 leading-relaxed">
            Design a network-based, game-theoretic model to analyze strategic
            interactions among financial institutions such as banks, exchanges,
            and clearing houses operating within a shared financial
            infrastructure.
          </p>

          {/* Description */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-8 mb-10 border border-red-900/30">
            <p className="text-lg text-gray-200 mb-6 leading-relaxed">
              The model should capture how local decisions such as credit
              provision, margin requirements, and trade routing interact through
              network connections like credit exposures and settlement
              obligations. These interactions should explain how individual
              incentives influence system-level outcomes including{" "}
              <span className="text-red-400 font-semibold">liquidity flow</span>
              , <span className="text-red-400 font-semibold">congestion</span>,{" "}
              <span className="text-red-400 font-semibold">systemic risk</span>,
              and{" "}
              <span className="text-red-400 font-semibold">
                financial stability
              </span>
              .
            </p>

            <p className="text-lg text-gray-200 mb-6 leading-relaxed">
              The system must account for strategic behavior under incomplete
              information and demonstrate how localized decisions propagate
              through the network to either strengthen resilience or trigger
              cascading failures.
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link
              to="/signup"
              className="px-8 py-4 bg-red-600 hover:bg-red-700 rounded-lg text-lg font-semibold transition transform hover:scale-105"
            >
              Get Started
            </Link>
            <Link
              to="/playground"
              className="px-8 py-4 bg-gray-700 hover:bg-gray-600 rounded-lg text-lg font-semibold transition transform hover:scale-105"
            >
              View Demo
            </Link>
          </div>

          {/* Business Impact Section */}
          <div className="bg-red-950/30 backdrop-blur-sm rounded-xl p-8 border border-red-800/50">
            <h2 className="text-3xl font-bold mb-4 text-red-400">
              Business Impact
            </h2>
            <p className="text-lg text-gray-200 leading-relaxed">
              This model helps regulators and financial institutions understand
              how micro-level decisions can create macro-level financial risks.
              By identifying fragile structures, bottlenecks, and incentive
              misalignments, the solution supports{" "}
              <span className="font-semibold text-red-300">
                better regulatory policies
              </span>
              ,{" "}
              <span className="font-semibold text-red-300">
                safer clearing mechanisms
              </span>
              ,{" "}
              <span className="font-semibold text-red-300">
                improved risk management
              </span>
              , and more resilient financial systems capable of withstanding
              economic shocks.
            </p>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="container mx-auto px-6 py-20">
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <div className="bg-gray-800/30 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-red-600 transition">
            <div className="text-4xl mb-4">🏦</div>
            <h3 className="text-xl font-bold mb-2 text-red-400">
              Strategic Analysis
            </h3>
            <p className="text-gray-300">
              Model strategic interactions among banks, exchanges, and clearing
              houses with game theory.
            </p>
          </div>

          <div className="bg-gray-800/30 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-red-600 transition">
            <div className="text-4xl mb-4">🔗</div>
            <h3 className="text-xl font-bold mb-2 text-red-400">
              Network Dynamics
            </h3>
            <p className="text-gray-300">
              Analyze how credit exposures and settlement obligations propagate
              through networks.
            </p>
          </div>

          <div className="bg-gray-800/30 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-red-600 transition">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-xl font-bold mb-2 text-red-400">
              Risk Assessment
            </h3>
            <p className="text-gray-300">
              Identify systemic risks, fragile structures, and potential
              cascading failures.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="container mx-auto px-6 py-8 text-center text-gray-400 border-t border-gray-800">
        <p>&copy; 2026 FinNet. Building resilient financial systems.</p>
      </footer>
    </div>
  );
}

export default HeroPage;
