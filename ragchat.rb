# Homebrew Formula for RAGChat
# To be hosted in your Homebrew tap repository: soumen888/homebrew-tap

class Ragchat < Formula
  desc "Universal Documentation & Community Chatbot (RAG)"
  homepage "https://github.com/soumen888/Rag-Chatbot"
  url "https://github.com/soumen888/Rag-Chatbot/archive/refs/heads/main.tar.gz"
  license "MIT"

  depends_on "python@3.11"

  def install
    venv = virtualenv_create(libexec, "python3.11")
    venv.pip_install resources
    venv.pip_install_and_link buildpath

    bin.install_symlink libexec/"bin/ragchat" => "ragchat"
  end

  test do
    system "#{bin}/ragchat", "--version"
  end
end
