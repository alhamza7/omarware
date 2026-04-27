import { User, Calendar, Clock } from 'lucide-react';

export function Header() {
  const currentDate = new Date().toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit' 
  });
  const currentTime = new Date().toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: true 
  });

  return (
    <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 shadow-lg">
      <div className="flex justify-between items-center max-w-[1800px] mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm">
            <span className="text-lg">🏪</span>
          </div>
          <h1 className="text-xl">NBS POS</h1>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-lg backdrop-blur-sm">
            <User className="w-4 h-4" />
            <span className="text-sm">User: Cashier</span>
          </div>
          <div className="flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-lg backdrop-blur-sm">
            <Calendar className="w-4 h-4" />
            <span className="text-sm">Safe: {currentDate}, 2:49:11 PM</span>
          </div>
          <div className="flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-lg backdrop-blur-sm">
            <Clock className="w-4 h-4" />
            <span className="text-sm">Time: {currentTime}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
