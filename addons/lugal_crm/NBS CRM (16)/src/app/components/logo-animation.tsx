import { motion } from "motion/react";
import logoImage from "../../assets/7128e639748d8ab0a0bb57260634200e94c7f43f.png";

export function LogoAnimation() {
  return (
    <motion.div 
      className="flex items-center gap-4"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* 3D Embossed Logo Button - Switch Style */}
      <motion.div 
        className="w-14 h-14 rounded-2xl bg-sidebar flex items-center justify-center relative overflow-hidden group cursor-pointer border border-sidebar-border/10"
        initial="initial"
        whileHover="hover"
        whileTap="tapped"
        variants={{
            initial: { 
                boxShadow: "6px 6px 12px rgba(0,0,0,0.6), -2px -2px 8px rgba(255,255,255,0.08)",
                scale: 1
            },
            hover: { 
                boxShadow: "8px 8px 16px rgba(0,0,0,0.7), -3px -3px 10px rgba(255,255,255,0.1)",
                scale: 1.02
            },
            tapped: { 
                boxShadow: "inset 4px 4px 8px rgba(0,0,0,0.7), inset -2px -2px 8px rgba(255,255,255,0.05)",
                scale: 0.95
            }
        }}
        transition={{ type: "spring", stiffness: 400, damping: 20 }}
      >
        {/* Inner glow on hover */}
        <div className="absolute inset-0 bg-gradient-to-tr from-primary/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
        
        <motion.img 
          src={logoImage} 
          alt="Noor Al Nibras Logo"
          className="w-9 h-9 object-contain drop-shadow-[0_4px_6px_rgba(0,0,0,0.3)]"
          variants={{
              initial: { rotate: 0, scale: 1 },
              hover: { rotate: 5, scale: 1.1 },
              tapped: { rotate: 0, scale: 0.95 }
          }}
          transition={{ duration: 0.4 }}
        />
      </motion.div>

      {/* Text Info */}
      <div className="flex flex-col select-none">
        <motion.h1 
          className="font-bold text-xl text-gradient-gold drop-shadow-sm tracking-tight"
          animate={{
            backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          نور النبراس
        </motion.h1>
        <motion.p 
          className="text-xs text-muted-foreground font-medium"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          تجارة العطور
        </motion.p>
      </div>
    </motion.div>
  );
}