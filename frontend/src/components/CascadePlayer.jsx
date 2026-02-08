import React, { useState, useEffect } from 'react';
import './CascadePlayer.css';

/**
 * CascadePlayer - Timeline controls for replaying cascade events
 * Allows step-by-step replay and visualization sync
 */
const CascadePlayer = ({ cascade, onStepChange, isPlaying, onPlayToggle }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [speed, setSpeed] = useState(1000); // ms per step

  const maxSteps = cascade?.affected_banks?.length || 0;

  // Auto-play
  useEffect(() => {
    if (isPlaying && currentStep < maxSteps) {
      const timer = setTimeout(() => {
        setCurrentStep(prev => Math.min(prev + 1, maxSteps));
      }, speed);
      return () => clearTimeout(timer);
    } else if (currentStep >= maxSteps && isPlaying) {
      onPlayToggle?.(false);
    }
  }, [isPlaying, currentStep, maxSteps, speed, onPlayToggle]);

  // Notify parent of step changes
  useEffect(() => {
    if (onStepChange) {
      onStepChange(currentStep);
    }
  }, [currentStep, onStepChange]);

  const handlePlayPause = () => {
    if (currentStep >= maxSteps) {
      setCurrentStep(0);
      onPlayToggle?.(true);
    } else {
      onPlayToggle?.(!isPlaying);
    }
  };

  const handleReset = () => {
    setCurrentStep(0);
    onPlayToggle?.(false);
  };

  const handleStepForward = () => {
    setCurrentStep(prev => Math.min(prev + 1, maxSteps));
    onPlayToggle?.(false);
  };

  const handleStepBackward = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
    onPlayToggle?.(false);
  };

  const handleSliderChange = (e) => {
    setCurrentStep(parseInt(e.target.value));
    onPlayToggle?.(false);
  };

  const handleSpeedChange = (newSpeed) => {
    setSpeed(newSpeed);
  };

  if (!cascade || maxSteps === 0) {
    return null;
  }

  const progress = (currentStep / maxSteps) * 100;

  return (
    <div className="cascade-player">
      <div className="player-header">
        <h4>🎬 Cascade Replay</h4>
        <div className="speed-controls">
          <button
            className={`speed-btn ${speed === 2000 ? 'active' : ''}`}
            onClick={() => handleSpeedChange(2000)}
          >
            0.5x
          </button>
          <button
            className={`speed-btn ${speed === 1000 ? 'active' : ''}`}
            onClick={() => handleSpeedChange(1000)}
          >
            1x
          </button>
          <button
            className={`speed-btn ${speed === 500 ? 'active' : ''}`}
            onClick={() => handleSpeedChange(500)}
          >
            2x
          </button>
        </div>
      </div>

      {/* Timeline Slider */}
      <div className="timeline-container">
        <div className="timeline-track">
          <div className="timeline-progress" style={{ width: `${progress}%` }}></div>
          <input
            type="range"
            min="0"
            max={maxSteps}
            value={currentStep}
            onChange={handleSliderChange}
            className="timeline-slider"
          />
        </div>
        <div className="timeline-labels">
          <span>Start</span>
          <span className="current-step">
            Step {currentStep}/{maxSteps}
          </span>
          <span>End</span>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="player-controls">
        <button
          className="control-btn reset-btn"
          onClick={handleReset}
          disabled={currentStep === 0}
          title="Reset to start"
        >
          ⏮️
        </button>
        <button
          className="control-btn step-btn"
          onClick={handleStepBackward}
          disabled={currentStep === 0}
          title="Step backward"
        >
          ⏪
        </button>
        <button
          className="control-btn play-btn"
          onClick={handlePlayPause}
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {currentStep >= maxSteps ? '🔄' : isPlaying ? '⏸️' : '▶️'}
        </button>
        <button
          className="control-btn step-btn"
          onClick={handleStepForward}
          disabled={currentStep >= maxSteps}
          title="Step forward"
        >
          ⏩
        </button>
      </div>

      {/* Current Bank Info */}
      {currentStep > 0 && cascade.affected_banks && (
        <div className="current-bank-info">
          <div className="bank-info-header">
            {currentStep === 1 ? '💥 Trigger Bank' : `⚠️ Cascade Wave ${currentStep}`}
          </div>
          <div className="bank-info-name">
            Bank {cascade.affected_banks[currentStep - 1]}
          </div>
        </div>
      )}
    </div>
  );
};

export default CascadePlayer;
