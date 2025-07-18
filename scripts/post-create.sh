#!/bin/bash

# git初期設定
git config --global user.name ${GIT_USER_NAME}
git config --global user.email ${GIT_USER_EMAIL}

# クローン先のディレクトリパス
APP_DIR="/workspace/app"

# ディレクトリが存在しない場合のみクローンを実行
if [ ! -d "${APP_DIR}/.git" ]; then
  echo "Cloning repository..."
  # APP_REPO_URLはdevcontainer.jsonから環境変数として渡される
  git clone $APP_REPO_URL ${APP_DIR}
else
  echo "Repository already exists. Skipping clone."
fi

# 依存関係のインストールなど、毎回実行したい処理はここに書く
cd ${APP_DIR}
npm install

echo "✅ Development environment setup complete."
