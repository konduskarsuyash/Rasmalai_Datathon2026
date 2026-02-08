import React, { useState, useEffect } from 'react';
import './CascadeVisualization.css';

/**
 * CascadeVisualization - Shows cascade events with animated spread visualization
 * Displays cascade depth, affected banks, and timeline of propagation
 */
const CascadeVisualization = ({ cascadeEvents, banks, onReplayCascade }) => {
  const [selectedCascade, setSelectedCascade] = useState(null);
  const [animationStep, setAnimationStep] = useState(0);

  // Auto-select latest cascade
  useEffect(() => {
    if (cascadeEvents && cascadeEvents.length > 0 && !selectedCascade) {
      setSelectedCascade(cascadeEvents[cascadeEvents.length - 1]);
    }
  }, [cascadeEvents, selectedCascade]);

  // Animate cascade spread
  useEffect(() => {
    if (selectedCascade && animationStep < selectedCascade.affected_banks?.length) {
      const timer = setTimeout(() => {
        setAnimationStep(prev => prev + 1);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [selectedCascade, animationStep]);

  if (!cascadeEvents || cascadeEvents.length === 0) {
    return (
      <div className="cascade-empty">
        <div className="cascade-empty-icon">🌊</div>
        <h3>No Cascades Detected</h3>
        <p>The system is stable. To test cascade effects, trigger a bank default.</p>
      </div>
    );
  }

  const handleSelectCascade = (cascade) => {
    setSelectedCascade(cascade);
    setAnimationStep(0);
  };

  const handleReplay = () => {
    setAnimationStep(0);
    if (onReplayCascade && selectedCascade) {
      onReplayCascade(selectedCascade);
    }
  };

  return (
    <div className="cascade-visualization">
      <div className="cascade-header">
        <h2>🌊 Cascade Events</h2>
        <div className="cascade-stats">
          <div className="stat-badge">
            <span className="stat-label">Total Cascades</span>
            <span className="stat-value">{cascadeEvents.length}</span>
          </div>
          <div className="stat-badge">
            <span className="stat-label">Total Affected</span>
            <span className="stat-value">
              {cascadeEvents.reduce((sum, c) => sum + (c.cascade_count || 0), 0)}
            </span>
          </div>
        </div>
      </div>

      <div className="cascade-content">
        {/* Cascade List */}
        <div className="cascade-list">
          <h3>Event Timeline</h3>
          {cascadeEvents.map((cascade, idx) => (
            <div
              key={idx}
              className={`cascade-item ${selectedCascade === cascade ? 'selected' : ''}`}
              onClick={() => handleSelectCascade(cascade)}
            >
              <div className="cascade-item-header">
                <span className="cascade-time">Step {cascade.time_step}</span>
                <span className={`cascade-severity severity-${cascade.cascade_count > 3 ? 'high' : cascade.cascade_count > 1 ? 'medium' : 'low'}`}>
                  {cascade.cascade_count} defaults
                </span>
              </div>
              <div className="cascade-item-depth">
                Cascade Depth: {cascade.cascade_depth || 1}
              </div>
            </div>
          ))}
        </div>

        {/* Cascade Details */}
        {selectedCascade && (
          <div className="cascade-details">
            <div className="cascade-details-header">
              <h3>Cascade Analysis</h3>
              <button className="replay-btn" onClick={handleReplay}>
                🔄 Replay
              </button>
            </div>

            <div className="cascade-info-grid">
              <div className="info-card">
                <div className="info-label">Trigger Time</div>
                <div className="info-value">Step {selectedCascade.time_step}</div>
              </div>
              <div className="info-card">
                <div className="info-label">Cascade Count</div>
                <div className="info-value">{selectedCascade.cascade_count}</div>
              </div>
              <div className="info-card">
                <div className="info-label">Cascade Depth</div>
                <div className="info-value">{selectedCascade.cascade_depth || 1}</div>
              </div>
              <div className="info-card">
                <div className="info-label">Total Affected</div>
                <div className="info-value">
                  {selectedCascade.affected_banks?.length || selectedCascade.cascade_count + 1}
                </div>
              </div>
            </div>

            {/* Cascade Spread Animation */}
            <div className="cascade-spread">
              <h4>Propagation Flow</h4>
              <div className="spread-timeline">
                {selectedCascade.affected_banks?.map((bankId, idx) => (
                  <div
                    key={bankId}
                    className={`spread-node ${idx < animationStep ? 'active' : ''} ${idx === 0 ? 'trigger' : ''}`}
                    style={{ animationDelay: `${idx * 0.5}s` }}
                  >
                    <div className="spread-node-icon">
                      {idx === 0 ? '💥' : '⚠️'}
                    </div>
                    <div className="spread-node-label">
                      {banks?.find(b => b.id === bankId)?.name || `Bank ${bankId}`}
                    </div>
                    <div className="spread-node-order">
                      {idx === 0 ? 'Trigger' : `Wave ${idx}`}
                    </div>
                  </div>
                )) || (
                  <div className="spread-placeholder">
                    No detailed bank information available
                  </div>
                )}
              </div>
            </div>

            {/* Cascade Waves Visualization */}
            {selectedCascade.cascade_depth > 0 && (
              <div className="cascade-waves">
                <h4>Cascade Waves</h4>
                <div className="waves-container">
                  {[...Array(selectedCascade.cascade_depth + 1)].map((_, waveIdx) => (
                    <div key={waveIdx} className="wave-level">
                      <div className="wave-number">Wave {waveIdx}</div>
                      <div className="wave-bar" style={{ width: `${100 - waveIdx * 20}%` }}>
                        <div className="wave-bar-inner"></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CascadeVisualization;
