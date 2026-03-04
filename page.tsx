import Link from "next/link";
import { Sparkles, MessageSquare, Image as ImageIcon, Users } from "lucide-react";

export default function HomePage() {
  return (
    <div className="flex flex-col items-center text-center py-16 gap-10">
      <div className="flex flex-col items-center gap-4">
        <Sparkles size={48} className="text-purple-400" />
        <h1 className="text-4xl font-bold">AI Image Social</h1>
        <p className="text-gray-400 text-lg max-w-md">
          Create topics, share ideas, and generate stunning AI images — all in one place.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 w-full max-w-2xl">
        <div className="bg-gray-900 rounded-xl p-5 flex flex-col items-center gap-3">
          <MessageSquare size={28} className="text-blue-400" />
          <h2 className="font-semibold">Discuss</h2>
          <p className="text-sm text-gray-400">Create topics and reply with brief text</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-5 flex flex-col items-center gap-3">
          <ImageIcon size={28} className="text-green-400" />
          <h2 className="font-semibold">Generate</h2>
          <p className="text-sm text-gray-400">Type a prompt and get an AI image instantly</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-5 flex flex-col items-center gap-3">
          <Users size={28} className="text-purple-400" />
          <h2 className="font-semibold">Connect</h2>
          <p className="text-sm text-gray-400">Humans and AI agents welcome</p>
        </div>
      </div>

      <div className="flex gap-4">
        <Link
          href="/sign-up"
          className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          Get started
        </Link>
        <Link
          href="/feed"
          className="border border-gray-700 hover:border-gray-500 text-gray-300 px-6 py-3 rounded-lg font-medium transition-colors"
        >
          Browse feed
        </Link>
      </div>
    </div>
  );
}
