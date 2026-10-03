import { motion } from 'framer-motion'
import { setMega, useMega } from '../mega'
import { sfx } from '../sound'

/** Bottom-right switch: when ON, every slot spin and roulette spin is a mega jackpot. */
export default function MegaToggle() {
  const on = useMega()
  return (
    <motion.button
      className={`mega-toggle ${on ? 'on' : ''}`} role="switch" aria-checked={on} aria-label="Mega jackpot mode"
      whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.94 }}
      onClick={() => { setMega(!on); on ? sfx.megaOff() : sfx.megaOn() }}
    >
      <span className="mega-ico">🎰</span>
      <span className="mega-text"><b>MEGA JACKPOT MODE</b><small>{on ? 'ON · every spin is a jackpot!' : 'OFF · normal odds'}</small></span>
      <span className="mega-switch"><i /></span>
    </motion.button>
  )
}
