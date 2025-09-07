import React from 'react'
import { motion } from 'framer-motion'
import { Card } from './Card'

interface AnimatedCardProps {
  children: React.ReactNode
  className?: string
  delay?: number
  hover?: boolean
  clickable?: boolean
  onClick?: () => void
}

export function AnimatedCard({ 
  children, 
  className = '', 
  delay = 0, 
  hover = true,
  clickable = false,
  onClick 
}: AnimatedCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      whileHover={hover ? { y: -5, scale: 1.02 } : {}}
      whileTap={clickable ? { scale: 0.98 } : {}}
      onClick={onClick}
      className={clickable ? 'cursor-pointer' : ''}
    >
      <Card className={className}>
        {children}
      </Card>
    </motion.div>
  )
}

interface StaggeredCardsProps {
  children: React.ReactNode[]
  className?: string
}

export function StaggeredCards({ children, className = '' }: StaggeredCardsProps) {
  return (
    <motion.div
      className={className}
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            staggerChildren: 0.1
          }
        }
      }}
    >
      {children.map((child, index) => (
        <motion.div
          key={index}
          variants={{
            hidden: { opacity: 0, y: 20 },
            visible: { opacity: 1, y: 0 }
          }}
          transition={{ duration: 0.5 }}
        >
          {child}
        </motion.div>
      ))}
    </motion.div>
  )
}
