class Ragchat < Formula
  desc "Universal Documentation RAG Chatbot for Websites, Telegram, and Discord"
  homepage "https://github.com/soumen888/Rag-Chatbot"
  url "https://github.com/soumen888/Rag-Chatbot/releases/download/v4.0.0/ragchat"
  sha256 "98ed87ca55f362c3da049972ad44d8e9668cd61460c24119629fb8a4192056a6"
  version "4.0.0"

  def install
    bin.install "ragchat"
  end

  test do
    system "#{bin}/ragchat", "--help"
  end
end
