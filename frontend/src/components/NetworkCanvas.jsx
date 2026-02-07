// components/NetworkCanvas.jsx
import { useRef, useEffect, useState } from "react";

const NetworkCanvas = ({
  institutions,
  connections,
  onSelectInstitution,
  onSelectConnection,
  onUpdateInstitution,
  onAddConnection,
  selectedInstitution,
  selectedConnection,
  isSimulating,
  zoomLevel = 1,
  tool = "select",
  activeTransactions = [],
  realtimeConnections = [],
}) => {
  const canvasRef = useRef(null);
  const [dragging, setDragging] = useState(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [pulsePhase, setPulsePhase] = useState(0);
  const [connectingFrom, setConnectingFrom] = useState(null);
  const [connectionEnd, setConnectionEnd] = useState(null);
  const animationFrameRef = useRef(null);

  // Animation loop
  useEffect(() => {
    const animate = () => {
      setPulsePhase((prev) => (prev + 0.05) % (Math.PI * 2));
      animationFrameRef.current = requestAnimationFrame(animate);
    };
    animate();
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    // Clear with clean white background
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Apply zoom transformation
    ctx.save();
    ctx.translate(canvas.width / 2, canvas.height / 2);
    ctx.scale(zoomLevel, zoomLevel);
    ctx.translate(-canvas.width / 2, -canvas.height / 2);

    // Draw enhanced grid
    drawModernGrid(ctx, canvas.width, canvas.height);

    // Draw connections with flow animation
    connections.forEach((conn) => {
      const source = institutions.find((i) => i.id === conn.source);
      const target = institutions.find((i) => i.id === conn.target);
      if (source && target) {
        drawAnimatedConnection(
          ctx,
          source,
          target,
          conn,
          selectedConnection?.id === conn.id,
        );
      }
    });

    // Draw real-time connections (from backend simulation)
    realtimeConnections.forEach((conn) => {
      const source = institutions.find((i) => i.id === `bank${conn.from + 1}`);
      const target = institutions.find((i) => i.id === `bank${conn.to + 1}`);
      if (source && target) {
        drawRealtimeConnection(ctx, source, target, conn);
      }
    });

    // Draw active transactions
    activeTransactions.forEach((tx) => {
      const source = institutions.find((i) => i.id === `bank${tx.from + 1}`);
      const target = tx.to !== null ? institutions.find((i) => i.id === `bank${tx.to + 1}`) : null;
      if (source) {
        drawTransaction(ctx, source, target, tx);
      }
    });

    // Draw institutions with pulse effect
    institutions.forEach((inst) => {
      drawModernInstitution(ctx, inst, selectedInstitution?.id === inst.id);
    });

    // Draw temporary connection line while dragging
    if (connectingFrom && connectionEnd) {
      const sourceInst = institutions.find((i) => i.id === connectingFrom);
      if (sourceInst) {
        const angle = Math.atan2(
          connectionEnd.y - sourceInst.position.y,
          connectionEnd.x - sourceInst.position.x,
        );
        const startX = sourceInst.position.x + Math.cos(angle) * 45;
        const startY = sourceInst.position.y + Math.sin(angle) * 45;

        ctx.strokeStyle = "#3b82f6";
        ctx.lineWidth = 3;
        ctx.setLineDash([8, 4]);
        ctx.shadowBlur = 12;
        ctx.shadowColor = "#3b82f6";
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(connectionEnd.x, connectionEnd.y);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.shadowBlur = 0;
      }
    }

    // Restore context after zoom transformation
    ctx.restore();
  }, [
    institutions,
    connections,
    selectedInstitution,
    selectedConnection,
    pulsePhase,
    connectingFrom,
    connectionEnd,
    zoomLevel,
    activeTransactions,
    realtimeConnections,
  ]);

  const drawModernGrid = (ctx, width, height) => {
    const gridSize = 40;

    // Light dots pattern for Canva-style board
    ctx.fillStyle = "rgba(203, 213, 225, 0.4)";
    for (let x = 0; x < width; x += gridSize) {
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.arc(x, y, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Light accent lines every 200px
    ctx.strokeStyle = "rgba(203, 213, 225, 0.25)";
    ctx.lineWidth = 1;

    for (let x = 0; x < width; x += 200) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    for (let y = 0; y < height; y += 200) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
  };

  const drawAnimatedConnection = (ctx, source, target, conn, isSelected) => {
    // Enhanced colors with neon effect
    const colors = {
      credit: { main: "#3b82f6", glow: "#60a5fa", accent: "#93c5fd" },
      settlement: { main: "#10b981", glow: "#34d399", accent: "#6ee7b7" },
      margin: { main: "#f59e0b", glow: "#fbbf24", accent: "#fcd34d" },
    };

    const colorScheme = colors[conn.type] || {
      main: "#6b7280",
      glow: "#9ca3af",
      accent: "#d1d5db",
    };

    const angle = Math.atan2(
      target.position.y - source.position.y,
      target.position.x - source.position.x,
    );

    const sourceRadius = 45;
    const targetRadius = 45;

    const startX = source.position.x + Math.cos(angle) * sourceRadius;
    const startY = source.position.y + Math.sin(angle) * sourceRadius;
    const endX = target.position.x - Math.cos(angle) * targetRadius;
    const endY = target.position.y - Math.sin(angle) * targetRadius;

    // Glow effect
    if (isSelected || isSimulating) {
      ctx.shadowBlur = 20;
      ctx.shadowColor = colorScheme.glow;
    } else {
      ctx.shadowBlur = 10;
      ctx.shadowColor = colorScheme.main;
    }

    // Main line with gradient
    const gradient = ctx.createLinearGradient(startX, startY, endX, endY);
    gradient.addColorStop(0, colorScheme.main);
    gradient.addColorStop(0.5, colorScheme.glow);
    gradient.addColorStop(1, colorScheme.main);

    ctx.strokeStyle = isSelected ? "#ef4444" : gradient;
    ctx.lineWidth = isSelected ? 4 : Math.max(2.5, conn.weight * 4);
    ctx.lineCap = "round";
    ctx.setLineDash(conn.type === "margin" ? [8, 4] : []);

    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();

    // Animated dollar sign particles during transfer
    if (isSimulating) {
      const particleCount = 3;
      for (let i = 0; i < particleCount; i++) {
        const t =
          ((pulsePhase + (i * Math.PI * 2) / particleCount) % (Math.PI * 2)) /
          (Math.PI * 2);
        const particleX = startX + (endX - startX) * t;
        const particleY = startY + (endY - startY) * t;

        // Draw dollar sign with edge
        ctx.save();
        ctx.shadowBlur = 12;
        ctx.shadowColor = colorScheme.main;

        // White circle background
        ctx.fillStyle = "#ffffff";
        ctx.beginPath();
        ctx.arc(particleX, particleY, 10, 0, Math.PI * 2);
        ctx.fill();

        // Colored border
        ctx.strokeStyle = colorScheme.main;
        ctx.lineWidth = 2;
        ctx.stroke();

        // Dollar sign
        ctx.fillStyle = colorScheme.main;
        ctx.font = "bold 14px system-ui";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("$", particleX, particleY);
        ctx.restore();
      }
    }

    ctx.setLineDash([]);
    ctx.shadowBlur = 0;

    // Arrowhead with glow
    const headlen = 16;
    ctx.beginPath();
    ctx.moveTo(endX, endY);
    ctx.lineTo(
      endX - headlen * Math.cos(angle - Math.PI / 6),
      endY - headlen * Math.sin(angle - Math.PI / 6),
    );
    ctx.lineTo(
      endX - headlen * Math.cos(angle + Math.PI / 6),
      endY - headlen * Math.sin(angle + Math.PI / 6),
    );
    ctx.closePath();
    ctx.fillStyle = isSelected ? "#ef4444" : colorScheme.glow;
    ctx.fill();

    // Exposure label with enhanced styling
    const midX = (startX + endX) / 2;
    const midY = (startY + endY) / 2;

    // Add subtle glow
    ctx.shadowBlur = 12;
    ctx.shadowColor = colorScheme.main;

    ctx.fillStyle = "#ffffff";
    ctx.strokeStyle = colorScheme.main;
    ctx.lineWidth = 2;

    ctx.beginPath();
    ctx.roundRect(midX - 32, midY - 12, 64, 24, 8);
    ctx.fill();
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.fillStyle = colorScheme.main;
    ctx.font = "bold 11px system-ui";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(`$${conn.exposure}M`, midX, midY);
  };

  const drawModernInstitution = (ctx, inst, isSelected) => {
    const { x, y } = inst.position;
    const radius = 45;
    const pulseScale = 1 + Math.sin(pulsePhase) * 0.05;

    // Outer glow ring with pulse
    if (isSelected || isSimulating) {
      const glowRadius = radius * pulseScale + 15;
      const gradient = ctx.createRadialGradient(x, y, radius, x, y, glowRadius);

      const typeColors = {
        bank: "rgba(59, 130, 246, 0.4)",
        exchange: "rgba(16, 185, 129, 0.4)",
        clearinghouse: "rgba(245, 158, 11, 0.4)",
      };

      gradient.addColorStop(
        0,
        typeColors[inst.type] || "rgba(107, 114, 128, 0.4)",
      );
      gradient.addColorStop(1, "transparent");

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(x, y, glowRadius, 0, Math.PI * 2);
      ctx.fill();
    }

    // Risk indicator ring
    const riskRadius = radius + 8;
    const riskColor = `rgba(${Math.floor(255 * inst.risk)}, ${Math.floor(255 * (1 - inst.risk))}, 80, 0.8)`;

    ctx.strokeStyle = riskColor;
    ctx.lineWidth = 4;
    ctx.shadowBlur = 10;
    ctx.shadowColor = riskColor;
    ctx.beginPath();
    ctx.arc(x, y, riskRadius, 0, Math.PI * 2 * inst.risk);
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Main institution circle with modern gradient
    const typeGradients = {
      bank: ["#3b82f6", "#1e40af"],
      exchange: ["#10b981", "#047857"],
      clearinghouse: ["#f59e0b", "#b45309"],
    };

    const [color1, color2] = typeGradients[inst.type] || ["#6b7280", "#374151"];
    const gradient = ctx.createRadialGradient(x, y - 15, 0, x, y, radius);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();

    // Border with double ring for selected
    if (isSelected) {
      ctx.shadowBlur = 20;
      ctx.shadowColor = color1;
      ctx.strokeStyle = color1;
      ctx.lineWidth = 4;
      ctx.stroke();

      ctx.strokeStyle = "rgba(255, 255, 255, 0.5)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y, radius + 5, 0, Math.PI * 2);
      ctx.stroke();
    } else {
      ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    ctx.shadowBlur = 0;

    // Draw proper SVG-style icons
    ctx.fillStyle = "#ffffff";
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    if (inst.type === "bank") {
      // Bank building icon
      ctx.beginPath();
      // Roof
      ctx.moveTo(x - 18, y - 8);
      ctx.lineTo(x, y - 18);
      ctx.lineTo(x + 18, y - 8);
      ctx.stroke();
      // Building body
      ctx.fillRect(x - 16, y - 8, 32, 24);
      // Columns
      ctx.fillStyle = color2;
      ctx.fillRect(x - 12, y - 4, 4, 16);
      ctx.fillRect(x - 4, y - 4, 4, 16);
      ctx.fillRect(x + 4, y - 4, 4, 16);
      ctx.fillRect(x + 12, y - 4, 4, 16);
      // Base
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(x - 18, y + 12, 36, 4);
    } else if (inst.type === "exchange") {
      // Stock chart icon
      ctx.beginPath();
      ctx.moveTo(x - 16, y + 8);
      ctx.lineTo(x - 10, y - 2);
      ctx.lineTo(x - 2, y + 4);
      ctx.lineTo(x + 6, y - 8);
      ctx.lineTo(x + 16, y + 2);
      ctx.stroke();
      // Points
      ctx.fillStyle = "#ffffff";
      [x - 16, x - 10, x - 2, x + 6, x + 16].forEach((px, idx) => {
        const py = [y + 8, y - 2, y + 4, y - 8, y + 2][idx];
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, Math.PI * 2);
        ctx.fill();
      });
    } else if (inst.type === "clearinghouse") {
      // Balance scale icon
      ctx.beginPath();
      // Stand
      ctx.moveTo(x, y - 12);
      ctx.lineTo(x, y + 12);
      ctx.stroke();
      // Base
      ctx.beginPath();
      ctx.moveTo(x - 12, y + 12);
      ctx.lineTo(x + 12, y + 12);
      ctx.stroke();
      // Beam
      ctx.beginPath();
      ctx.moveTo(x - 16, y - 8);
      ctx.lineTo(x + 16, y - 8);
      ctx.stroke();
      // Left pan
      ctx.beginPath();
      ctx.arc(x - 12, y - 2, 6, 0, Math.PI, true);
      ctx.stroke();
      // Right pan
      ctx.beginPath();
      ctx.arc(x + 12, y - 2, 6, 0, Math.PI, true);
      ctx.stroke();
    }

    // Capital value inside node
    ctx.font = "bold 11px system-ui";
    ctx.fillStyle = "rgba(255, 255, 255, 0.85)";
    ctx.fillText(`$${Math.round(inst.capital)}M`, x, y + 20);

    // Name label with enhanced styling - fixed position below node
    ctx.font = "bold 12px system-ui";
    const textWidth = ctx.measureText(inst.name).width;
    const labelY = y + radius + 12;

    // Subtle glow for name background
    ctx.shadowBlur = 12;
    ctx.shadowColor = color1;

    ctx.fillStyle = "#ffffff";
    ctx.strokeStyle = color1;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(x - textWidth / 2 - 10, labelY - 10, textWidth + 20, 20, 8);
    ctx.fill();
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.fillStyle = color2;
    ctx.textBaseline = "middle";
    ctx.fillText(inst.name, x, labelY);

    // Status indicator dot
    const statusColor =
      inst.risk > 0.7 ? "#ef4444"
      : inst.risk > 0.4 ? "#f59e0b"
      : "#10b981";
    ctx.fillStyle = statusColor;
    ctx.shadowBlur = 8;
    ctx.shadowColor = statusColor;
    ctx.beginPath();
    ctx.arc(x + radius - 10, y - radius + 10, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
  };

  const drawRealtimeConnection = (ctx, source, target, conn) => {
    // Draw real-time connection in bright cyan
    const angle = Math.atan2(
      target.position.y - source.position.y,
      target.position.x - source.position.x,
    );

    const sourceRadius = 45;
    const targetRadius = 45;

    const startX = source.position.x + Math.cos(angle) * sourceRadius;
    const startY = source.position.y + Math.sin(angle) * sourceRadius;
    const endX = target.position.x - Math.cos(angle) * targetRadius;
    const endY = target.position.y - Math.sin(angle) * targetRadius;

    // Bright animated connection
    ctx.shadowBlur = 20;
    ctx.shadowColor = "#06b6d4";

    const gradient = ctx.createLinearGradient(startX, startY, endX, endY);
    gradient.addColorStop(0, "#06b6d4");
    gradient.addColorStop(0.5, "#0891b2");
    gradient.addColorStop(1, "#06b6d4");

    ctx.strokeStyle = gradient;
    ctx.lineWidth = 4;
    ctx.lineCap = "round";

    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();

    ctx.shadowBlur = 0;

    // Arrowhead
    const headlen = 16;
    ctx.beginPath();
    ctx.moveTo(endX, endY);
    ctx.lineTo(
      endX - headlen * Math.cos(angle - Math.PI / 6),
      endY - headlen * Math.sin(angle - Math.PI / 6),
    );
    ctx.lineTo(
      endX - headlen * Math.cos(angle + Math.PI / 6),
      endY - headlen * Math.sin(angle + Math.PI / 6),
    );
    ctx.closePath();
    ctx.fillStyle = "#0891b2";
    ctx.fill();

    // Amount label
    const midX = (startX + endX) / 2;
    const midY = (startY + endY) / 2;

    ctx.shadowBlur = 12;
    ctx.shadowColor = "#06b6d4";

    ctx.fillStyle = "#ffffff";
    ctx.strokeStyle = "#06b6d4";
    ctx.lineWidth = 2;

    ctx.beginPath();
    ctx.roundRect(midX - 28, midY - 12, 56, 24, 8);
    ctx.fill();
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.fillStyle = "#0891b2";
    ctx.font = "bold 11px system-ui";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(`$${conn.amount.toFixed(1)}M`, midX, midY);
  };

  const drawTransaction = (ctx, source, target, tx) => {
    if (!target) {
      // Market transaction or cash hoarding - show at source
      ctx.save();
      ctx.shadowBlur = 20;
      ctx.shadowColor = "#f59e0b";

      // Pulsing circle at source
      const pulseSize = 20 + Math.sin(Date.now() / 100) * 5;
      
      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.arc(source.position.x, source.position.y, pulseSize, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = "#f59e0b";
      ctx.lineWidth = 3;
      ctx.stroke();

      // Transaction label
      ctx.fillStyle = "#f59e0b";
      ctx.font = "bold 12px system-ui";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(tx.action.replace(/_/g, ' '), source.position.x, source.position.y);
      
      ctx.restore();
      return;
    }

    // Bank-to-bank transaction - animate along path
    const angle = Math.atan2(
      target.position.y - source.position.y,
      target.position.x - source.position.x,
    );

    const sourceRadius = 45;
    const targetRadius = 45;

    const startX = source.position.x + Math.cos(angle) * sourceRadius;
    const startY = source.position.y + Math.sin(angle) * sourceRadius;
    const endX = target.position.x - Math.cos(angle) * targetRadius;
    const endY = target.position.y - Math.sin(angle) * targetRadius;

    // Animated particle moving along path
    const progress = ((Date.now() % 2000) / 2000);
    const txX = startX + (endX - startX) * progress;
    const txY = startY + (endY - startY) * progress;

    ctx.save();
    ctx.shadowBlur = 25;
    ctx.shadowColor = "#10b981";

    // Large glowing circle
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(txX, txY, 18, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = "#10b981";
    ctx.lineWidth = 4;
    ctx.stroke();

    // Amount inside
    ctx.shadowBlur = 0;
    ctx.fillStyle = "#10b981";
    ctx.font = "bold 14px system-ui";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(`$${tx.amount.toFixed(0)}`, txX, txY);

    ctx.restore();
  };

  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Check if clicking on an institution
    const clicked = institutions.find((inst) => {
      const dx = x - inst.position.x;
      const dy = y - inst.position.y;
      return Math.sqrt(dx * dx + dy * dy) < 45;
    });

    if (clicked) {
      onSelectInstitution(clicked);
      if (!isSimulating) {
        // Ctrl/Cmd + drag to create connection
        if (e.ctrlKey || e.metaKey) {
          setConnectingFrom(clicked.id);
          setConnectionEnd({ x, y });
        } else {
          // Regular drag to move node
          setDragging(clicked.id);
          setOffset({ x: x - clicked.position.x, y: y - clicked.position.y });
        }
      }
    } else {
      onSelectInstitution(null);
    }
  };

  const handleMouseMove = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Update connection end point while dragging
    if (connectingFrom) {
      setConnectionEnd({ x, y });
      return;
    }

    // Move node
    if (dragging && !isSimulating) {
      onUpdateInstitution(dragging, {
        position: { x: x - offset.x, y: y - offset.y },
      });
    }
  };

  const handleMouseUp = (e) => {
    // Complete connection creation
    if (connectingFrom) {
      const rect = canvasRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Find target institution
      const target = institutions.find((inst) => {
        if (inst.id === connectingFrom) return false; // Can't connect to self
        const dx = x - inst.position.x;
        const dy = y - inst.position.y;
        return Math.sqrt(dx * dx + dy * dy) < 45;
      });

      if (target && onAddConnection) {
        // Create connection with default values
        onAddConnection(connectingFrom, target.id, "credit", 100);
      }

      setConnectingFrom(null);
      setConnectionEnd(null);
    }

    setDragging(null);
  };

  return (
    <canvas
      ref={canvasRef}
      className={`w-full h-full backdrop-blur-sm ${connectingFrom ? "cursor-crosshair" : "cursor-pointer"}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={() => {
        setDragging(null);
        setConnectingFrom(null);
        setConnectionEnd(null);
      }}
    />
  );
};

export default NetworkCanvas;
