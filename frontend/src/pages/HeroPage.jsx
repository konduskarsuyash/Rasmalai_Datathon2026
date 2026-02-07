import { Link } from "react-router-dom";
import { useUser, SignOutButton } from "@clerk/clerk-react";
import { useState, useEffect } from "react";

function HeroPage() {
  const { isSignedIn, user } = useUser();
  const [activeCard, setActiveCard] = useState(null);
  const [showLogoAnimation, setShowLogoAnimation] = useState(true);
  const [animationComplete, setAnimationComplete] = useState(false);

  // Logo animation effect
  useEffect(() => {
    // After 2.5 seconds, start moving logo to navbar
    const timer1 = setTimeout(() => {
      setAnimationComplete(true);
    }, 2500);

    // After 3 seconds, hide the center animation completely
    const timer2 = setTimeout(() => {
      setShowLogoAnimation(false);
    }, 3000);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, []);

  // Animated network background effect
  useEffect(() => {
    const canvas = document.getElementById('network-bg');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const nodes = Array.from({ length: 40 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      radius: Math.random() * 1.5 + 0.5
    }));

    function animate() {
      ctx.fillStyle = 'rgba(248, 250, 252, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      nodes.forEach((node, i) => {
        node.x += node.vx;
        node.y += node.vy;

        if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
        if (node.y < 0 || node.y > canvas.height) node.vy *= -1;

        // Draw connections
        nodes.slice(i + 1).forEach(other => {
          const dx = other.x - node.x;
          const dy = other.y - node.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 120) {
            ctx.strokeStyle = `rgba(29, 78, 216, ${0.1 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(other.x, other.y);
            ctx.stroke();
          }
        });

        // Draw nodes
        ctx.fillStyle = 'rgba(14, 165, 164, 0.4)';
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fill();
      });

      requestAnimationFrame(animate);
    }

    animate();

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#111827] overflow-x-hidden">
      {/* Logo Loading Animation */}
      {showLogoAnimation && (
        <div 
          className={`fixed inset-0 bg-[#F8FAFC] flex items-center justify-center transition-all duration-700 ${
            animationComplete ? 'opacity-0 pointer-events-none' : 'opacity-100 z-[9999]'
          }`}
        >
          <div className="relative">
            {/* Rotating Square */}
            <div 
              className="absolute -left-16 top-1/2 transform -translate-y-1/2"
              style={{
                animation: 'orbitSquare 2s ease-in-out'
              }}
            >
              <div 
                className="w-16 h-16 bg-[#1D4ED8] rounded transform rotate-45"
                style={{
                  animation: 'spinSquare 2s linear infinite'
                }}
              />
            </div>
            
            {/* Logo Text */}
            <div 
              className="text-6xl font-bold tracking-tight"
              style={{
                animation: 'fadeInScale 1s ease-out'
              }}
            >
              <span className="text-[#0F172A]">Fin</span>
              <span className="text-[#1D4ED8]">Net</span>
            </div>
          </div>
        </div>
      )}

      {/* Animated Network Background */}
      <canvas 
        id="network-bg" 
        className="fixed inset-0 pointer-events-none opacity-20"
        style={{ zIndex: 0 }}
      />

      {/* Content Wrapper */}
      <div className="relative" style={{ zIndex: 1 }}>
        {/* Navigation Bar */}
        <nav 
          className={`fixed top-0 w-full bg-white/95 backdrop-blur-lg border-b border-[#E5E7EB] z-50 shadow-sm transition-all duration-700 ${
            animationComplete ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-full'
          }`}
        >
          <div className="container mx-auto px-6 py-4 flex justify-between items-center">
            <div 
              className="flex items-center space-x-2"
              style={{
                animation: animationComplete ? 'slideInFromCenter 0.7s ease-out' : 'none'
              }}
            >
              <div 
                className="w-8 h-8 bg-[#1D4ED8] rounded transform rotate-45"
                style={{
                  animation: 'continuousSpin 4s linear infinite'
                }}
              />
              <span className="text-xl font-bold tracking-tight">
                <span className="text-[#0F172A]">Fin</span>
                <span className="text-[#1D4ED8]">Net</span>
              </span>
            </div>
            <div className="flex items-center space-x-6">
              {isSignedIn ? (
                <>
                  <Link
                    to="/playground"
                    className="text-sm text-[#475569] hover:text-[#1D4ED8] transition font-medium"
                  >
                    Simulation Lab
                  </Link>
                  <div className="flex items-center space-x-3 pl-6 border-l border-[#E5E7EB]">
                    <div className="w-8 h-8 bg-[#1D4ED8] rounded-full flex items-center justify-center text-xs font-bold text-white">
                      {user?.firstName?.[0] || user?.primaryEmailAddress?.emailAddress[0].toUpperCase()}
                    </div>
                    <span className="text-[#111827] text-sm font-medium">
                      {user?.firstName || user?.primaryEmailAddress?.emailAddress?.split('@')[0]}
                    </span>
                    <SignOutButton>
                      <button className="px-4 py-2 text-sm bg-[#F8FAFC] hover:bg-[#E5E7EB] rounded-lg transition border border-[#E5E7EB]">
                        Sign Out
                      </button>
                    </SignOutButton>
                  </div>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="px-4 py-2 text-sm text-[#475569] hover:text-[#1D4ED8] transition font-medium"
                  >
                    Login
                  </Link>
                  <Link
                    to="/signup"
                    className="px-6 py-2 text-sm bg-[#1D4ED8] hover:bg-[#2563EB] text-white rounded-lg transition font-medium"
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section 
          className={`pt-32 pb-20 px-6 transition-all duration-1000 ${
            animationComplete ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
          }`}
        >
          <div className="container mx-auto max-w-6xl">
            <div className="text-center mb-12">
              <div className="inline-block px-4 py-1.5 bg-[#DBEAFE] border border-[#93C5FD] rounded-full mb-6">
                <span className="text-[#1D4ED8] text-sm font-medium tracking-wide">
                  SYSTEMIC RISK RESEARCH PLATFORM
                </span>
              </div>
              
              <h1 className="text-5xl md:text-7xl font-bold mb-8 leading-tight tracking-tight text-[#0F172A]">
                Network-Based<br />
                <span className="text-[#1D4ED8]">
                  Game-Theoretic Modeling
                </span>
                <br />
                of Financial Infrastructure
              </h1>

              <p className="text-xl md:text-2xl text-[#475569] mb-12 max-w-4xl mx-auto leading-relaxed font-light">
                How micro-level decisions create macro-level financial risk.
                <br />
                Analyzing strategic interactions, network contagion, and systemic resilience.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
                <Link
                  to="/playground"
                  className="group px-8 py-4 bg-[#1D4ED8] hover:bg-[#2563EB] text-white rounded-lg text-lg font-semibold transition transform hover:scale-105 shadow-lg"
                >
                  Explore the Model
                  <span className="inline-block ml-2 group-hover:translate-x-1 transition-transform">→</span>
                </Link>
                <button className="px-8 py-4 bg-white hover:bg-[#F8FAFC] text-[#0F172A] rounded-lg text-lg font-semibold transition border-2 border-[#0F172A] transform hover:scale-105">
                  Download Research Brief
                </button>
              </div>

              <div className="flex items-center justify-center space-x-8 text-sm text-[#6B7280]">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-[#16A34A] rounded-full animate-pulse" />
                  <span>Real-time Network Simulation</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-[#0EA5A4] rounded-full animate-pulse" />
                  <span>Game-Theoretic Analysis</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Problem Statement */}
        <section className="py-20 px-6 bg-white">
          <div className="container mx-auto max-w-6xl">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="text-3xl md:text-4xl font-bold mb-6 text-[#0F172A]">
                  The Hidden Architecture of <span className="text-[#1D4ED8]">Financial Fragility</span>
                </h2>
                <p className="text-[#475569] mb-4 leading-relaxed">
                  Modern financial systems are characterized by deep fragmentation and hidden interdependencies. 
                  Credit exposures, settlement obligations, and margin requirements create complex networks where 
                  individual incentives often conflict with systemic stability.
                </p>
                <p className="text-[#475569] mb-4 leading-relaxed">
                  Traditional risk models fail to capture how strategic behavior under incomplete information 
                  propagates through these networks—turning local shocks into cascading failures.
                </p>
                <p className="text-[#475569] leading-relaxed">
                  Without visibility into network bottlenecks and incentive misalignments, regulators and 
                  institutions operate blind to the mechanisms that amplify systemic risk.
                </p>
              </div>
              <div className="bg-white border-2 border-[#E5E7EB] rounded-2xl p-8 shadow-lg">
                <div className="space-y-6">
                  <div className="flex items-start space-x-4">
                    <div className="w-12 h-12 bg-[#FEF3C7] border border-[#FDE68A] rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-2xl">⚠️</span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-[#111827] mb-1">Fragmented Visibility</h3>
                      <p className="text-sm text-[#6B7280]">No unified view of network-wide exposures and dependencies</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-4">
                    <div className="w-12 h-12 bg-[#CFFAFE] border border-[#A5F3FC] rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-2xl">🔗</span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-[#111827] mb-1">Hidden Interdependencies</h3>
                      <p className="text-sm text-[#6B7280]">Opaque counterparty chains amplify contagion risk</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-4">
                    <div className="w-12 h-12 bg-[#FECACA] border border-[#FCA5A5] rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-2xl">💥</span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-[#111827] mb-1">Cascading Failures</h3>
                      <p className="text-sm text-[#6B7280]">Localized decisions trigger system-wide collapses</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Solution Overview */}
        <section className="py-20 px-6 bg-[#F8FAFC]">
          <div className="container mx-auto max-w-6xl">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold mb-6 text-[#0F172A]">
                A New Framework for <span className="text-[#1D4ED8]">Systemic Resilience</span>
              </h2>
              <p className="text-xl text-[#475569] max-w-3xl mx-auto">
                Our network-based game-theoretic model treats financial institutions as strategic agents 
                operating under incomplete information, revealing how local actions propagate to create 
                system-wide outcomes.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-white border-2 border-[#E5E7EB] rounded-xl p-6 hover:border-[#1D4ED8] hover:shadow-xl transition-all duration-300">
                <div className="text-3xl mb-4">🎯</div>
                <h3 className="text-xl font-bold mb-3 text-[#0F172A]">Strategic Agents</h3>
                <p className="text-[#475569] text-sm leading-relaxed">
                  Banks, exchanges, and clearing houses modeled as rational players optimizing under constraints and uncertainty.
                </p>
              </div>

              <div className="bg-white border-2 border-[#E5E7EB] rounded-xl p-6 hover:border-[#1D4ED8] hover:shadow-xl transition-all duration-300">
                <div className="text-3xl mb-4">🌐</div>
                <h3 className="text-xl font-bold mb-3 text-[#0F172A]">Network Topology</h3>
                <p className="text-[#475569] text-sm leading-relaxed">
                  Credit exposures, settlement obligations, and margin requirements mapped as weighted, directed graphs.
                </p>
              </div>

              <div className="bg-white border-2 border-[#E5E7EB] rounded-xl p-6 hover:border-[#1D4ED8] hover:shadow-xl transition-all duration-300">
                <div className="text-3xl mb-4">📈</div>
                <h3 className="text-xl font-bold mb-3 text-[#0F172A]">Equilibrium Dynamics</h3>
                <p className="text-[#475569] text-sm leading-relaxed">
                  Nash equilibria reveal how incentive structures shape liquidity flow, congestion, and systemic stability.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Core Capabilities */}
        <section className="py-20 px-6 bg-white">
          <div className="container mx-auto max-w-6xl">
            <h2 className="text-4xl font-bold text-center mb-16 text-[#0F172A]">
              Core <span className="text-[#1D4ED8]">Capabilities</span>
            </h2>

            <div className="grid md:grid-cols-2 gap-8">
              {[
                {
                  icon: '🏦',
                  title: 'Strategic Agent Modeling',
                  description: 'Simulate banks, exchanges, and clearing houses with heterogeneous risk appetites, capital constraints, and information sets.'
                },
                {
                  icon: '💸',
                  title: 'Credit Exposure Networks',
                  description: 'Map bilateral exposures and counterparty dependencies to identify central nodes and systemic importance.'
                },
                {
                  icon: '🔄',
                  title: 'Settlement Flow Analysis',
                  description: 'Trace payment obligations through the network to detect bottlenecks and liquidity pressure points.'
                },
                {
                  icon: '📊',
                  title: 'Margin Policy Incentives',
                  description: 'Analyze how margin requirements and collateral rules affect risk-taking and network structure.'
                },
                {
                  icon: '⚡',
                  title: 'Stress Testing',
                  description: 'Inject shocks to simulate default cascades, liquidity freezes, and fire-sale contagion mechanisms.'
                },
                {
                  icon: '🎯',
                  title: 'Trade Routing Optimization',
                  description: 'Model how institutions route trades strategically, creating concentration risk and fragile dependencies.'
                }
              ].map((capability, idx) => (
                <div
                  key={idx}
                  onMouseEnter={() => setActiveCard(idx)}
                  onMouseLeave={() => setActiveCard(null)}
                  className={`bg-white border-2 rounded-xl p-8 transition-all duration-300 ${
                    activeCard === idx ? 'border-[#1D4ED8] shadow-2xl scale-105' : 'border-[#E5E7EB]'
                  }`}
                >
                  <div className="text-4xl mb-4">{capability.icon}</div>
                  <h3 className="text-xl font-bold mb-3 text-[#0F172A]">{capability.title}</h3>
                  <p className="text-[#475569] leading-relaxed">{capability.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Systemic Risk Insights */}
        <section className="py-20 px-6 bg-[#F8FAFC]">
          <div className="container mx-auto max-w-6xl">
            <div className="bg-white border-2 border-[#E5E7EB] rounded-2xl p-12 shadow-lg">
              <h2 className="text-3xl md:text-4xl font-bold mb-8 text-center text-[#0F172A]">
                Systemic Risk & <span className="text-[#1D4ED8]">Stability Insights</span>
              </h2>
              
              <div className="grid md:grid-cols-3 gap-8 mb-8">
                <div className="text-center">
                  <div className="text-5xl font-bold text-[#1D4ED8] mb-2">85%</div>
                  <div className="text-sm text-[#6B7280]">Cascading failure events predicted before occurrence</div>
                </div>
                <div className="text-center">
                  <div className="text-5xl font-bold text-[#1D4ED8] mb-2">3.2x</div>
                  <div className="text-sm text-[#6B7280]">Faster bottleneck identification vs traditional methods</div>
                </div>
                <div className="text-center">
                  <div className="text-5xl font-bold text-[#1D4ED8] mb-2">40%</div>
                  <div className="text-sm text-[#6B7280]">Reduction in systemic risk through incentive redesign</div>
                </div>
              </div>

              <div className="space-y-6 mt-12">
                <div className="flex items-start space-x-4 bg-[#F8FAFC] rounded-lg p-6 border border-[#E5E7EB]">
                  <div className="text-2xl">🔬</div>
                  <div>
                    <h4 className="font-semibold text-[#111827] mb-2">Equilibrium Emergence</h4>
                    <p className="text-[#475569] text-sm">
                      Observe how Nash equilibria form under different regulatory regimes and network topologies, 
                      revealing stable vs unstable configurations.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4 bg-[#F8FAFC] rounded-lg p-6 border border-[#E5E7EB]">
                  <div className="text-2xl">🌊</div>
                  <div>
                    <h4 className="font-semibold text-[#111827] mb-2">Fragile Network Structures</h4>
                    <p className="text-[#475569] text-sm">
                      Identify how core-periphery patterns and hub concentration amplify shocks, 
                      and test interventions to strengthen resilience.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4 bg-[#F8FAFC] rounded-lg p-6 border border-[#E5E7EB]">
                  <div className="text-2xl">🛡️</div>
                  <div>
                    <h4 className="font-semibold text-[#111827] mb-2">Resilience Through Redesign</h4>
                    <p className="text-[#475569] text-sm">
                      Simulate policy changes—capital buffers, liquidity requirements, position limits—to 
                      realign incentives and prevent systemic breakdowns.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Business Impact */}
        <section className="py-20 px-6 bg-white">
          <div className="container mx-auto max-w-6xl">
            <h2 className="text-4xl font-bold text-center mb-16 text-[#0F172A]">
              Business & <span className="text-[#1D4ED8]">Regulatory Impact</span>
            </h2>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white border-2 border-[#E5E7EB] rounded-xl p-6 text-center hover:border-[#1D4ED8] hover:shadow-xl transition-all">
                <div className="text-3xl mb-3">🏛️</div>
                <h3 className="font-bold text-[#111827] mb-2">Smarter Policy</h3>
                <p className="text-sm text-[#6B7280]">Evidence-based regulatory frameworks grounded in network dynamics</p>
              </div>

              <div className="bg-white border-2 border-[#E5E7EB] rounded-xl p-6 text-center hover:border-[#1D4ED8] hover:shadow-xl transition-all">
                <div className="text-3xl mb-3">⚖️</div>
                <h3 className="font-bold text-[#111827] mb-2">Safer Clearing</h3>
                <p className="text-sm text-[#6B7280]">Optimized margin and settlement mechanisms that reduce counterparty risk</p>
              </div>

              <div className="bg-white border-2 border-[#E5E7EB] rounded-xl p-6 text-center hover:border-[#1D4ED8] hover:shadow-xl transition-all">
                <div className="text-3xl mb-3">📉</div>
                <h3 className="font-bold text-[#111827] mb-2">Risk Reduction</h3>
                <p className="text-sm text-[#6B7280]">Preemptive identification of systemic vulnerabilities before crises emerge</p>
              </div>

              <div className="bg-white border-2 border-[#E5E7EB] rounded-xl p-6 text-center hover:border-[#1D4ED8] hover:shadow-xl transition-all">
                <div className="text-3xl mb-3">🎯</div>
                <h3 className="font-bold text-[#111827] mb-2">Crisis Preparedness</h3>
                <p className="text-sm text-[#6B7280]">Scenario planning and stress testing for economic shocks</p>
              </div>
            </div>
          </div>
        </section>

        {/* Use Cases */}
        <section className="py-20 px-6 bg-[#F8FAFC]">
          <div className="container mx-auto max-w-6xl">
            <h2 className="text-4xl font-bold text-center mb-16 text-[#0F172A]">
              Built for <span className="text-[#1D4ED8]">Decision Makers</span>
            </h2>

            <div className="space-y-6">
              <div className="bg-white border-2 border-[#E5E7EB] rounded-xl p-8 hover:border-[#1D4ED8] hover:shadow-xl transition-all">
                <div className="flex items-start space-x-6">
                  <div className="w-16 h-16 bg-[#DBEAFE] border border-[#93C5FD] rounded-xl flex items-center justify-center flex-shrink-0">
                    <span className="text-3xl">🏦</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold mb-2 text-[#0F172A]">Central Banks</h3>
                    <p className="text-[#475569]">
                      Monitor systemic risk in real-time, identify systemically important institutions, 
                      and design macroprudential interventions that account for strategic responses.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white border-2 border-[#E5E7EB] rounded-xl p-8 hover:border-[#1D4ED8] hover:shadow-xl transition-all">
                <div className="flex items-start space-x-6">
                  <div className="w-16 h-16 bg-[#DBEAFE] border border-[#93C5FD] rounded-xl flex items-center justify-center flex-shrink-0">
                    <span className="text-3xl">⚖️</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold mb-2 text-[#0F172A]">Financial Regulators</h3>
                    <p className="text-[#475569]">
                      Test policy interventions—capital requirements, leverage ratios, position limits—before 
                      implementation to understand second-order effects.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white border-2 border-[#E5E7EB] rounded-xl p-8 hover:border-[#1D4ED8] hover:shadow-xl transition-all">
                <div className="flex items-start space-x-6">
                  <div className="w-16 h-16 bg-[#DBEAFE] border border-[#93C5FD] rounded-xl flex items-center justify-center flex-shrink-0">
                    <span className="text-3xl">🏢</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold mb-2 text-[#0F172A]">Financial Institutions</h3>
                    <p className="text-[#475569]">
                      Optimize counterparty exposure, stress-test credit portfolios, and develop trading 
                      strategies that balance profitability with systemic stability.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white border-2 border-[#E5E7EB] rounded-xl p-8 hover:border-[#1D4ED8] hover:shadow-xl transition-all">
                <div className="flex items-start space-x-6">
                  <div className="w-16 h-16 bg-[#DBEAFE] border border-[#93C5FD] rounded-xl flex items-center justify-center flex-shrink-0">
                    <span className="text-3xl">🔬</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold mb-2 text-[#0F172A]">Researchers & Academia</h3>
                    <p className="text-[#475569]">
                      Analyze financial contagion mechanisms, publish peer-reviewed research on network effects, 
                      and advance the theory of systemic risk.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-20 px-6 bg-white border-t-2 border-[#E5E7EB]">
          <div className="container mx-auto max-w-4xl text-center">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-[#0F172A]">
              Ready to Strengthen <span className="text-[#1D4ED8]">Financial Resilience?</span>
            </h2>
            <p className="text-xl text-[#475569] mb-12 max-w-2xl mx-auto">
              Join central banks, regulators, and leading institutions using network-based game theory 
              to build more resilient financial systems.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Link
                to="/playground"
                className="px-8 py-4 bg-[#1D4ED8] hover:bg-[#2563EB] text-white rounded-lg text-lg font-semibold transition transform hover:scale-105 shadow-lg"
              >
                Launch Simulation Lab
              </Link>
              <button className="px-8 py-4 bg-white hover:bg-[#F8FAFC] text-[#0F172A] rounded-lg text-lg font-semibold transition border-2 border-[#0F172A]">
                Download Whitepaper
              </button>
              <button className="px-8 py-4 bg-white hover:bg-[#F8FAFC] text-[#0F172A] rounded-lg text-lg font-semibold transition border-2 border-[#E5E7EB]">
                Schedule Demo
              </button>
            </div>

            <div className="flex items-center justify-center space-x-12 text-sm text-[#6B7280]">
              <div className="flex flex-col items-center">
                <div className="text-2xl font-bold text-[#0F172A] mb-1">500+</div>
                <div>Simulations Run</div>
              </div>
              <div className="flex flex-col items-center">
                <div className="text-2xl font-bold text-[#0F172A] mb-1">50+</div>
                <div>Institutions</div>
              </div>
              <div className="flex flex-col items-center">
                <div className="text-2xl font-bold text-[#0F172A] mb-1">15+</div>
                <div>Research Papers</div>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t-2 border-[#E5E7EB] bg-[#F8FAFC]">
          <div className="container mx-auto px-6 py-12">
            <div className="grid md:grid-cols-4 gap-8 mb-8">
              <div>
                <div className="flex items-center space-x-2 mb-4">
                  <div className="w-8 h-8 bg-[#1D4ED8] rounded transform rotate-45" />
                  <span className="text-xl font-bold">
                    <span className="text-[#0F172A]">Fin</span>
                    <span className="text-[#1D4ED8]">Net</span>
                  </span>
                </div>
                <p className="text-sm text-[#6B7280]">
                  Building resilient financial systems through network science and game theory.
                </p>
              </div>
              
              <div>
                <h4 className="font-semibold text-[#111827] mb-3">Platform</h4>
                <ul className="space-y-2 text-sm text-[#6B7280]">
                  <li><Link to="/playground" className="hover:text-[#1D4ED8] transition">Simulation Lab</Link></li>
                  <li><a href="#" className="hover:text-[#1D4ED8] transition">Documentation</a></li>
                  <li><a href="#" className="hover:text-[#1D4ED8] transition">API Access</a></li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold text-[#111827] mb-3">Research</h4>
                <ul className="space-y-2 text-sm text-[#6B7280]">
                  <li><a href="#" className="hover:text-[#1D4ED8] transition">Whitepapers</a></li>
                  <li><a href="#" className="hover:text-[#1D4ED8] transition">Case Studies</a></li>
                  <li><a href="#" className="hover:text-[#1D4ED8] transition">Methodology</a></li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold text-[#111827] mb-3">Company</h4>
                <ul className="space-y-2 text-sm text-[#6B7280]">
                  <li><a href="#" className="hover:text-[#1D4ED8] transition">About</a></li>
                  <li><a href="#" className="hover:text-[#1D4ED8] transition">Team</a></li>
                  <li><a href="#" className="hover:text-[#1D4ED8] transition">Contact</a></li>
                </ul>
              </div>
            </div>
            
            <div className="border-t-2 border-[#E5E7EB] pt-8 flex flex-col md:flex-row justify-between items-center text-sm text-[#6B7280]">
              <p>&copy; 2026 FinNet. All rights reserved.</p>
              <div className="flex space-x-6 mt-4 md:mt-0">
                <a href="#" className="hover:text-[#1D4ED8] transition">Privacy Policy</a>
                <a href="#" className="hover:text-[#1D4ED8] transition">Terms of Service</a>
                <a href="#" className="hover:text-[#1D4ED8] transition">Cookie Policy</a>
              </div>
            </div>
          </div>
        </footer>
      </div>

      {/* CSS Animations */}
      <style jsx>{`
        @keyframes fadeInScale {
          0% {
            opacity: 0;
            transform: scale(0.8);
          }
          100% {
            opacity: 1;
            transform: scale(1);
          }
        }

        @keyframes orbitSquare {
          0% {
            transform: translateX(0) translateY(0%) rotate(0deg);
          }
          50% {
            transform: translateX(-80px) translateY(0%) rotate(180deg);
          }
          100% {
            transform: translateX(0) translateY(0%) rotate(360deg);
          }
        }

        @keyframes spinSquare {
          0% {
            transform: rotate(45deg);
          }
          100% {
            transform: rotate(405deg);
          }
        }

        @keyframes continuousSpin {
          0% {
            transform: rotate(45deg);
          }
          100% {
            transform: rotate(405deg);
          }
        }

        @keyframes slideInFromCenter {
          0% {
            opacity: 0;
            transform: translateX(30vw) scale(1.5);
          }
          100% {
            opacity: 1;
            transform: translateX(0) scale(1);
          }
        }
      `}</style>
    </div>
  );
}

export default HeroPage;