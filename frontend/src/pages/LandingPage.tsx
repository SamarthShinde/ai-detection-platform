import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, Upload, Zap, FileText, ChevronDown, Check, Star } from 'lucide-react'
import { useState } from 'react'

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } },
}

const stagger = {
  visible: { transition: { staggerChildren: 0.1 } },
}

const features = [
  { icon: <Zap className="w-6 h-6" />, title: 'Real-time Detection', desc: 'Get results in seconds, not minutes. Our ML pipeline processes media at lightning speed.' },
  { icon: <Shield className="w-6 h-6" />, title: '99%+ Accuracy', desc: 'EfficientNet + Xception ensemble delivers state-of-the-art deepfake detection accuracy.' },
  { icon: <Upload className="w-6 h-6" />, title: 'Batch Processing', desc: 'Upload hundreds of files at once. Process entire datasets with a single API call.' },
  { icon: <FileText className="w-6 h-6" />, title: 'Export Results', desc: 'Download detailed reports as PDF, JSON, or CSV for integration with your workflow.' },
  { icon: <Star className="w-6 h-6" />, title: 'API Access', desc: 'Full REST API with JWT authentication. Integrate deepfake detection into any app.' },
  { icon: <Shield className="w-6 h-6" />, title: 'Enterprise Grade', desc: 'SOC2-ready infrastructure, audit logs, and dedicated support for large organizations.' },
]

const faqs = [
  { q: 'How accurate is the detection?', a: 'Our ensemble model (EfficientNet-B4 + Xception) achieves 99%+ accuracy on benchmark datasets. The confidence score helps you understand certainty for each result.' },
  { q: 'What file formats are supported?', a: 'Images: JPEG, PNG, WebP up to 100MB. Videos: MP4, AVI, MOV up to 100MB. More formats coming soon.' },
  { q: 'Is my data stored after analysis?', a: 'Files are stored securely during processing. You can delete your uploads at any time from the dashboard. We never sell or share your data.' },
  { q: 'Can I export results?', a: 'Yes! Export individual detections as JSON, or batch results as CSV or PDF report. Results include full model breakdown and frame-level analysis for videos.' },
  { q: 'Do you offer API access?', a: 'Yes, all plans include API access with JWT authentication. Generate API keys from your dashboard and integrate detection into any application.' },
]

const pricingTiers = [
  {
    name: 'Free',
    price: '$0',
    period: '/month',
    scans: '5 scans',
    features: ['Image detection', '5 scans/month', 'JSON export', 'API access', 'Email support'],
    cta: 'Get Started',
    highlight: false,
  },
  {
    name: 'Pro',
    price: '$9.99',
    period: '/month',
    scans: '100 scans',
    features: ['Image + Video detection', '100 scans/month', 'Batch processing', 'PDF/CSV export', 'Priority support'],
    cta: 'Start Free Trial',
    highlight: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    scans: 'Unlimited',
    features: ['Unlimited scans', 'Dedicated infrastructure', 'SLA guarantee', 'SSO / SAML', 'Custom integrations'],
    cta: 'Contact Sales',
    highlight: false,
  },
]

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border border-slate-700 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 text-left text-slate-100 hover:bg-slate-800/50 transition-colors"
      >
        <span className="font-medium">{q}</span>
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0 ml-4" />
        </motion.span>
      </button>
      <motion.div
        initial={false}
        animate={{ height: open ? 'auto' : 0, opacity: open ? 1 : 0 }}
        transition={{ duration: 0.25 }}
        className="overflow-hidden"
      >
        <p className="px-6 pb-4 text-slate-400 text-sm leading-relaxed">{a}</p>
      </motion.div>
    </div>
  )
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Nav */}
      <nav className="border-b border-slate-800 px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-xl">DeepDetect</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/auth" className="text-slate-400 hover:text-white text-sm transition-colors">
            Sign In
          </Link>
          <Link
            to="/auth"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Try Free
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden px-6 pt-20 pb-32">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 via-transparent to-purple-600/10 pointer-events-none" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/5 rounded-full blur-3xl pointer-events-none" />

        <motion.div
          initial="hidden"
          animate="visible"
          variants={stagger}
          className="max-w-4xl mx-auto text-center relative"
        >
          <motion.div variants={fadeUp} className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-sm mb-6">
            <Zap className="w-3.5 h-3.5" />
            Powered by EfficientNet-B4 + Xception
          </motion.div>

          <motion.h1 variants={fadeUp} className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
            Detect{' '}
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              AI-Generated
            </span>
            <br />
            Media Instantly
          </motion.h1>

          <motion.p variants={fadeUp} className="text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
            Military-grade deepfake detection for images and videos. Real-time results,
            batch processing, and full API access.
          </motion.p>

          <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link
              to="/auth"
              className="px-8 py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all hover:scale-105 active:scale-95"
            >
              Start Free — No card required
            </Link>
            <a
              href="#how-it-works"
              className="px-8 py-3.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl border border-slate-700 transition-all hover:scale-105 active:scale-95"
            >
              See How It Works
            </a>
          </motion.div>

          <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-8 justify-center">
            {[
              { value: '10,000+', label: 'Detections analyzed' },
              { value: '99.2%', label: 'Detection accuracy' },
              { value: '<10ms', label: 'Average latency' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl font-bold text-white">{stat.value}</div>
                <div className="text-sm text-slate-500 mt-1">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="px-6 py-24 bg-slate-800/30">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={stagger}
            className="text-center mb-16"
          >
            <motion.h2 variants={fadeUp} className="text-3xl font-bold mb-4">How It Works</motion.h2>
            <motion.p variants={fadeUp} className="text-slate-400 max-w-lg mx-auto">
              Three simple steps to verify any media file
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={stagger}
            className="grid md:grid-cols-3 gap-8"
          >
            {[
              { step: '01', icon: <Upload className="w-8 h-8" />, title: 'Upload', desc: 'Drag and drop your image or video. Supports all major formats up to 100MB.' },
              { step: '02', icon: <Zap className="w-8 h-8" />, title: 'Analyze', desc: 'Our AI ensemble runs deep analysis across 10+ detection layers in real-time.' },
              { step: '03', icon: <FileText className="w-8 h-8" />, title: 'Report', desc: 'Get a detailed probability score, confidence rating, and artifact breakdown.' },
            ].map((step) => (
              <motion.div
                key={step.step}
                variants={fadeUp}
                whileHover={{ scale: 1.03, y: -4 }}
                className="bg-slate-800 rounded-2xl p-8 border border-slate-700 text-center transition-shadow hover:shadow-xl hover:shadow-blue-500/5"
              >
                <div className="text-xs font-bold text-blue-400 mb-4 tracking-wider">{step.step}</div>
                <div className="w-16 h-16 bg-blue-600/20 text-blue-400 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  {step.icon}
                </div>
                <h3 className="text-xl font-bold mb-3">{step.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{step.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-24">
        <div className="max-w-6xl mx-auto">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="text-center mb-16">
            <motion.h2 variants={fadeUp} className="text-3xl font-bold mb-4">Everything You Need</motion.h2>
            <motion.p variants={fadeUp} className="text-slate-400 max-w-lg mx-auto">Powerful features built for developers, journalists, and enterprises</motion.p>
          </motion.div>
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <motion.div
                key={f.title}
                variants={fadeUp}
                whileHover={{ scale: 1.02, y: -2 }}
                className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-blue-500/30 transition-all"
              >
                <div className="w-12 h-12 bg-blue-600/20 text-blue-400 rounded-xl flex items-center justify-center mb-4">
                  {f.icon}
                </div>
                <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Pricing */}
      <section className="px-6 py-24 bg-slate-800/30">
        <div className="max-w-5xl mx-auto">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="text-center mb-16">
            <motion.h2 variants={fadeUp} className="text-3xl font-bold mb-4">Simple Pricing</motion.h2>
            <motion.p variants={fadeUp} className="text-slate-400">Start free, scale when you need</motion.p>
          </motion.div>
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="grid md:grid-cols-3 gap-6">
            {pricingTiers.map((tier) => (
              <motion.div
                key={tier.name}
                variants={fadeUp}
                className={`rounded-2xl p-8 border flex flex-col ${
                  tier.highlight
                    ? 'bg-blue-600/10 border-blue-500 scale-105 shadow-xl shadow-blue-500/10'
                    : 'bg-slate-800 border-slate-700'
                }`}
              >
                {tier.highlight && (
                  <div className="text-xs font-bold text-blue-400 bg-blue-500/20 px-3 py-1 rounded-full mb-4 text-center w-fit mx-auto">
                    MOST POPULAR
                  </div>
                )}
                <div className="mb-2 text-lg font-bold">{tier.name}</div>
                <div className="flex items-end gap-1 mb-1">
                  <span className="text-4xl font-bold">{tier.price}</span>
                  <span className="text-slate-400 mb-1">{tier.period}</span>
                </div>
                <div className="text-sm text-slate-400 mb-6">{tier.scans}</div>
                <ul className="space-y-3 mb-8 flex-1">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-slate-300">
                      <Check className="w-4 h-4 text-green-400 flex-shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to="/auth"
                  className={`w-full py-3 rounded-xl font-semibold text-center text-sm transition-all hover:scale-105 ${
                    tier.highlight
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : 'bg-slate-700 hover:bg-slate-600 text-white'
                  }`}
                >
                  {tier.cta}
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* FAQ */}
      <section className="px-6 py-24">
        <div className="max-w-3xl mx-auto">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="text-center mb-16">
            <motion.h2 variants={fadeUp} className="text-3xl font-bold mb-4">Frequently Asked Questions</motion.h2>
          </motion.div>
          <div className="space-y-3">
            {faqs.map((faq) => (
              <FAQItem key={faq.q} q={faq.q} a={faq.a} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Footer */}
      <section className="px-6 py-24 bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-t border-slate-800">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-4">Ready to detect deepfakes?</h2>
          <p className="text-slate-400 mb-8">Join thousands of professionals using DeepDetect to verify media authenticity.</p>
          <Link
            to="/auth"
            className="inline-flex px-10 py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-all hover:scale-105 text-lg"
          >
            Get Started Free
          </Link>
          <p className="text-slate-500 text-sm mt-4">No credit card required. 5 free scans every month.</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 border-t border-slate-800 text-center text-slate-500 text-sm">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-400" />
            <span className="text-slate-400 font-medium">DeepDetect</span>
          </div>
          <p>© 2026 DeepDetect. All rights reserved.</p>
          <div className="flex gap-4">
            <a href="#" className="hover:text-slate-300 transition-colors">Privacy</a>
            <a href="#" className="hover:text-slate-300 transition-colors">Terms</a>
            <a href="#" className="hover:text-slate-300 transition-colors">API Docs</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
