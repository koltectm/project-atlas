import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { clsx } from 'clsx'

const WIDTHS = { sm:'max-w-md', md:'max-w-lg', lg:'max-w-2xl', xl:'max-w-4xl', full:'max-w-7xl' }

export function Modal({ isOpen, onClose, title, children, size='md', footer }) {
  useEffect(() => {
    if (!isOpen) return
    const handler=(e)=>{ if(e.key==='Escape') onClose() }
    document.addEventListener('keydown',handler)
    document.body.style.overflow='hidden'
    return ()=>{ document.removeEventListener('keydown',handler); document.body.style.overflow='' }
  }, [isOpen, onClose])

  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <motion.div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
          initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} transition={{duration:0.15}}
          onClick={(e)=>{ if(e.target===e.currentTarget) onClose() }}>
          <motion.div role="dialog" aria-modal="true"
            className={clsx('w-full bg-surface-800 border border-surface-500 rounded-2xl shadow-2xl flex flex-col max-h-[90vh]', WIDTHS[size])}
            initial={{opacity:0,scale:0.95,y:8}} animate={{opacity:1,scale:1,y:0}} exit={{opacity:0,scale:0.95,y:8}} transition={{duration:0.2,ease:'easeOut'}}>
            <div className="flex items-center justify-between px-6 py-4 border-b border-surface-500 flex-shrink-0">
              <h2 className="text-base font-semibold text-white">{title}</h2>
              <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-white hover:bg-surface-600 transition-colors"><X className="w-4 h-4" /></button>
            </div>
            <div className="flex-1 overflow-y-auto px-6 py-5">{children}</div>
            {footer && <div className="flex-shrink-0 px-6 py-4 border-t border-surface-500 flex items-center justify-end gap-3">{footer}</div>}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  )
}
