interface SpeakerCounterProps {
  value: number;
  onChange: (num: number) => void;
  disabled?: boolean;
}

const SpeakerIllustration = ({ count }: { count: number }) => {
  const getSizePercent = (count: number) => {
    const sizes = {
      1: 40,
      2: 34,
      3: 28,
      4: 24,
      5: 21,
      6: 19,
      7: 17,
      8: 16,
      9: 20,
      10: 19
    };
    return sizes[count as keyof typeof sizes];
  };

  const generatePositions = () => {
    const positions: Array<{ x: number; y: number; id: number; delay: number }> = [];
    const sizePercent = getSizePercent(count);
    const iconRadius = sizePercent / 2;
    const maxRadius = 50 - iconRadius;
    const maxAttempts = 1000;

    for (let id = 1; id <= count; id++) {
      let placed = false;
      let attempts = 0;

      while (!placed && attempts < maxAttempts) {
        attempts++;

        const angle = Math.random() * 2 * Math.PI;
        const radius = maxRadius * Math.sqrt(Math.random());

        const x = 50 + radius * Math.cos(angle);
        const y = 50 + radius * Math.sin(angle);

        if (
          x - iconRadius < 0 ||
          x + iconRadius > 100 ||
          y - iconRadius < 0 ||
          y + iconRadius > 100
        ) {
          continue;
        }

        let overlap = false;
        for (const pos of positions) {
          const dx = x - pos.x;
          const dy = y - pos.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          if (distance < iconRadius * 2) {
            overlap = true;
            break;
          }
        }

        if (!overlap) {
          positions.push({
            x,
            y,
            id,
            delay: id * 0.1,
          });
          placed = true;
        }
      }

      if (!placed) {
        console.warn(`Could not place icon ${id} without overlap.`);
      }
    }

    return positions;
  };

  const speakers = generatePositions();
  const sizePercent = getSizePercent(count);

  return (
    <div className="absolute inset-0 top-0 bottom-12">
      <div className="relative w-full h-full">
        {speakers.map((pos) => (
          <div
            key={pos.id}
            className="absolute transition-all duration-300 ease-in-out 
                     hover:scale-110 hover:-translate-y-1 hover:z-10
                     animate-float"
            style={{
              left: `${pos.x}%`,
              top: `${pos.y}%`,
              width: `${sizePercent}%`,
              height: '0',
              paddingBottom: `${sizePercent}%`,
              transform: 'translate(-50%, -50%)',
              animation: `float 3s ease-in-out infinite ${pos.delay}s`,
            }}
          >
            <img
              src={`https://api.dicebear.com/7.x/notionists/svg?seed=${pos.id}&&backgroundType=gradientLinear&backgroundColor=c0aede,ffdfbf`}
              alt={`Speaker ${pos.id}`}
              className="absolute inset-0 w-full h-full rounded-full shadow-lg 
                       transition-shadow duration-300 
                       hover:shadow-indigo-500/25 hover:shadow-xl"
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default function SpeakerCounter({ value, onChange, disabled }: SpeakerCounterProps) {
  const percentage = ((value - 1) / 9) * 100;
  
  return (
    <div className="space-y-6">
      <label className="block text-sm font-medium text-gray-200">
        Number of Speakers: {value}
      </label>
      <div className="w-full h-64 relative">
        <SpeakerIllustration count={value} />
        <div className="absolute -bottom-4 left-0 right-0 pb-2">
          <div className="relative flex items-center mb-6">
            {/* Background track */}
            <div className="absolute inset-0 h-2 rounded-lg bg-gray-800/50"></div>
            {/* Gradient fill */}
            <div 
              className="absolute h-2 rounded-lg bg-gradient-to-r from-[#ff7eb3] via-[#e056fd] to-[#8957ff]"
              style={{ width: `${percentage}%` }}
            ></div>
            {/* Slider input */}
            <input
              type="range"
              min="1"
              max="10"
              value={value}
              onChange={(e) => onChange(parseInt(e.target.value))}
              disabled={disabled}
              className="
                relative z-10 w-full h-2
                appearance-none bg-transparent
                [&::-webkit-slider-thumb]:appearance-none
                [&::-webkit-slider-thumb]:h-5
                [&::-webkit-slider-thumb]:w-5
                [&::-webkit-slider-thumb]:rounded-full
                [&::-webkit-slider-thumb]:bg-gradient-to-r
                [&::-webkit-slider-thumb]:from-[#ff7eb3]
                [&::-webkit-slider-thumb]:to-[#8957ff]
                [&::-webkit-slider-thumb]:shadow-md
                [&::-webkit-slider-thumb]:border-2
                [&::-webkit-slider-thumb]:border-white/30
                [&::-webkit-slider-thumb]:cursor-pointer
              "
            />
          </div>
          {/* Numbers */}
          <div className="flex justify-between px-1">
            {[...Array(10)].map((_, i) => (
              <span 
                key={i}
                className={`text-xs ${value === i + 1 ? 'text-gray-200' : 'text-gray-400'}`}
              >
                {i + 1}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}