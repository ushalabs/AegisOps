import Link from "next/link";
import { ArrowLeft, ShieldAlert } from "lucide-react";
import { Panel } from "@/components/ui";

export default function NotFound() {
  return <div className="mx-auto max-w-2xl py-16"><Panel className="p-10 text-center"><div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[22px] bg-[#fff0ec]"><ShieldAlert className="h-7 w-7 text-[#d94d43]" /></div><h2 className="mt-5 text-2xl font-black">Record not found</h2><p className="mt-2 text-sm text-[#777b84]">The requested AegisOps record does not exist or is no longer available.</p><Link href="/" className="mt-6 inline-flex items-center gap-2 rounded-full bg-[#111625] px-5 py-3 text-xs font-black text-white"><ArrowLeft className="h-4 w-4" />Back to dashboard</Link></Panel></div>;
}
