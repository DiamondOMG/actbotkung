'use client';

interface StartButtonProps {
  active: boolean;
  onClick: () => void;
}

export function StartButton({ active, onClick }: StartButtonProps) {
  return (
    <button 
      onClick={onClick} 
      style={{ 
        width: 200, 
        height: 200, 
        borderRadius: '50%', 
        border: 'none', 
        background: active ? '#f44' : '#44f', 
        color: '#fff', 
        fontSize: 24, 
        cursor: 'pointer',
        boxShadow: active ? '0 0 50px #f44' : '0 0 20px #44f', 
        transition: '0.3s'
      }}
    >
      {active ? 'Stop' : 'Start'}
    </button>
  );
}
