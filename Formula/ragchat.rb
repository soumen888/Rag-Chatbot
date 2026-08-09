class Ragchat < Formula
  desc "Universal Documentation RAG Chatbot for Websites, Telegram, and Discord"
  homepage "https://github.com/soumen888/Rag-Chatbot"
  url "https://github.com/soumen888/Rag-Chatbot/releases/download/v4.0.0/ragchat-macos-x64"
  version "4.0.0"

  def install
    bin.install "ragchat-macos-x64" => "ragchat"
  end

  test do
    system "#{bin}/ragchat", "--help"
  end
end
