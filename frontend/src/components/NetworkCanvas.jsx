// components/NetworkCanvas.jsx
import { useRef, useEffect, useState } from 'react';

const NetworkCanvas = ({ 
  institutions, 
  connections, 
  onSelectInstitution, 
  onSelectConnection,
  onUpdateInstitution,
  selectedInstitution,
  selectedConnection,
  isSimulating 
}) => {
  const canvasRef = useRef(null);
  const [dragging, setDragging] = useState(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw grid
    drawGrid(ctx, canvas.width, canvas.height);

    // Draw connections
    connections.forEach(conn => {
      const source = institutions.find(i => i.id === conn.source);
      const target = institutions.find(i => i.id === conn.target);
      if (source && target) {
        drawConnection(ctx, source, target, conn, selectedConnection?.id === conn.id);
      }
    });

    // Draw institutions
    institutions.forEach(inst => {
      drawInstitution(ctx, inst, selectedInstitution?.id === inst.id);
    });

  }, [institutions, connections, selectedInstitution, selectedConnection]);

  const drawGrid = (ctx, width, height) => {
    ctx.strokeStyle = '#1f2937';
    ctx.lineWidth = 1;
    
    // Vertical lines
    for (let x = 0; x < width; x += 50) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    
    // Horizontal lines
    for (let y = 0; y < height; y += 50) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
  };

  const drawConnection = (ctx, source, target, conn, isSelected) => {
    const gradient = ctx.createLinearGradient(
      source.position.x, source.position.y,
      target.position.x, target.position.y
    );
    
    // Color based on connection type
    const colors = {
      credit: ['#3b82f6', '#60a5fa'],
      settlement: ['#10b981', '#34d399'],
      margin: ['#f59e0b', '#fbbf24']
    };
    
    const [color1, color2] = colors[conn.type] || ['#6b7280', '#9ca3af'];
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);

    ctx.strokeStyle = isSelected ? '#f87171' : gradient;
    ctx.lineWidth = isSelected ? 4 : Math.max(2, conn.weight * 5);
    ctx.setLineDash(conn.type === 'margin' ? [5, 5] : []);

    // Draw arrow
    const angle = Math.atan2(
      target.position.y - source.position.y,
      target.position.x - source.position.x
    );
    
    const sourceRadius = 40;
    const targetRadius = 40;
    
    const startX = source.position.x + Math.cos(angle) * sourceRadius;
    const startY = source.position.y + Math.sin(angle) * sourceRadius;
    const endX = target.position.x - Math.cos(angle) * targetRadius;
    const endY = target.position.y - Math.sin(angle) * targetRadius;

    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();

    // Draw arrowhead
    const headlen = 15;
    ctx.beginPath();
    ctx.moveTo(endX, endY);
    ctx.lineTo(
      endX - headlen * Math.cos(angle - Math.PI / 6),
      endY - headlen * Math.sin(angle - Math.PI / 6)
    );
    ctx.lineTo(
      endX - headlen * Math.cos(angle + Math.PI / 6),
      endY - headlen * Math.sin(angle + Math.PI / 6)
    );
    ctx.closePath();
    ctx.fillStyle = isSelected ? '#f87171' : color2;
    ctx.fill();

    ctx.setLineDash([]);

    // Draw exposure label
    const midX = (startX + endX) / 2;
    const midY = (startY + endY) / 2;
    ctx.fillStyle = '#1f2937';
    ctx.fillRect(midX - 25, midY - 10, 50, 20);
    ctx.fillStyle = '#ffffff';
    ctx.font = '11px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`$${conn.exposure}M`, midX, midY + 4);
  };

  const drawInstitution = (ctx, inst, isSelected) => {
    const { x, y } = inst.position;
    const radius = 40;

    // Glow effect for selected
    if (isSelected) {
      ctx.shadowBlur = 20;
      ctx.shadowColor = '#3b82f6';
    }

    // Background circle with risk color
    const riskColor = `rgba(${Math.floor(255 * inst.risk)}, ${Math.floor(255 * (1 - inst.risk))}, 100, 0.3)`;
    ctx.fillStyle = riskColor;
    ctx.beginPath();
    ctx.arc(x, y, radius + 10, 0, Math.PI * 2);
    ctx.fill();

    // Main circle based on type
    const typeColors = {
      bank: '#3b82f6',
      exchange: '#10b981',
      clearinghouse: '#f59e0b'
    };
    
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
    gradient.addColorStop(0, typeColors[inst.type] || '#6b7280');
    gradient.addColorStop(1, '#1f2937');
    
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();

    // Border
    ctx.strokeStyle = isSelected ? '#60a5fa' : '#374151';
    ctx.lineWidth = isSelected ? 3 : 2;
    ctx.stroke();

    ctx.shadowBlur = 0;

    // Icon/Type indicator
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const icons = {
      bank: '🏦',
      exchange: '📊',
      clearinghouse: '⚖️'
    };
    ctx.fillText(icons[inst.type] || '?', x, y - 8);

    // Capital indicator
    ctx.font = '11px Arial';
    ctx.fillText(`$${Math.round(inst.capital)}M`, x, y + 10);

    // Name label
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 12px Arial';
    const textWidth = ctx.measureText(inst.name).width;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(x - textWidth / 2 - 5, y + radius + 5, textWidth + 10, 20);
    ctx.fillStyle = '#ffffff';
    ctx.fillText(inst.name, x, y + radius + 17);

    // Risk indicator
    const riskBarWidth = 60;
    const riskBarHeight = 6;
    ctx.fillStyle = '#374151';
    ctx.fillRect(x - riskBarWidth / 2, y - radius - 15, riskBarWidth, riskBarHeight);
    ctx.fillStyle = `rgb(${Math.floor(255 * inst.risk)}, ${Math.floor(255 * (1 - inst.risk))}, 100)`;
    ctx.fillRect(x - riskBarWidth / 2, y - radius - 15, riskBarWidth * inst.risk, riskBarHeight);
  };

  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Check if clicking on an institution
    const clicked = institutions.find(inst => {
      const dx = x - inst.position.x;
      const dy = y - inst.position.y;
      return Math.sqrt(dx * dx + dy * dy) < 40;
    });

    if (clicked) {
      onSelectInstitution(clicked);
      if (!isSimulating) {
        setDragging(clicked.id);
        setOffset({ x: x - clicked.position.x, y: y - clicked.position.y });
      }
    } else {
      onSelectInstitution(null);
    }
  };

  const handleMouseMove = (e) => {
    if (!dragging || isSimulating) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    onUpdateInstitution(dragging, {
      position: { x: x - offset.x, y: y - offset.y }
    });
  };

  const handleMouseUp = () => {
    setDragging(null);
  };

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full cursor-pointer"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    />
  );
};

export default NetworkCanvas;