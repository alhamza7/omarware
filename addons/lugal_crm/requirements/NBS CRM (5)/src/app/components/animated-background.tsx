import { motion } from "motion/react";

export function AnimatedBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      {/* Animated gradient orbs */}
      <motion.div
        className="absolute top-0 right-0 w-[600px] h-[600px] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(240, 196, 25, 0.15) 0%, transparent 70%)",
          filter: "blur(60px)",
        }}
        animate={{
          x: [0, 100, 0],
          y: [0, 50, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      <motion.div
        className="absolute bottom-0 left-0 w-[500px] h-[500px] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(253, 245, 230, 0.1) 0%, transparent 70%)",
          filter: "blur(80px)",
        }}
        animate={{
          x: [0, -80, 0],
          y: [0, -60, 0],
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <motion.div
        className="absolute top-1/2 left-1/2 w-[400px] h-[400px] rounded-full -translate-x-1/2 -translate-y-1/2"
        style={{
          background: "radial-gradient(circle, rgba(240, 196, 25, 0.08) 0%, transparent 70%)",
          filter: "blur(70px)",
        }}
        animate={{
          scale: [1, 1.3, 1],
          rotate: [0, 180, 360],
        }}
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: "linear",
        }}
      />

      {/* Floating particles */}
      {[...Array(15)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-primary/20 rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [0, -30, 0],
            opacity: [0.2, 0.8, 0.2],
          }}
          transition={{
            duration: 3 + Math.random() * 3,
            repeat: Infinity,
            delay: Math.random() * 2,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}
