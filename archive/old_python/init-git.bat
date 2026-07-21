@echo off
REM ===========================================
REM  init-git.bat — привязка C:\Projects\MiniMax\BIT_Tech к GitHub
REM  Запустить ОДИН РАЗ из PowerShell: .\init-git.bat
REM ===========================================

cd /d C:\Projects\MiniMax\BIT_Tech

echo.
echo === 1/8 Backing up .env ===
if exist .env (
    copy /Y .env .env.bak >nul
    echo    .env saved to .env.bak
) else (
    echo    .env not found - skip
)

echo.
echo === 2/8 Removing old archives ===
del /Q "bit-technolog-prototype v0.1*" 2>nul
del /Q "bit-technolog-prototype v0.1.2*" 2>nul
echo    done

echo.
echo === 3/8 Writing .gitignore ===
> .gitignore (
echo # secrets
echo .env
echo .env.bak
echo .env.local
echo.
echo # runtime
echo bit_technolog.db
echo *.sqlite*
echo server.log
echo.
echo # python
echo __pycache__/
echo *.pyc
echo venv/
echo env/
echo.
echo # archives
echo *.tar.gz
echo *.zip
)
echo    done

echo.
echo === 4/8 Disabling SSL verify for git (corporate proxy) ===
git config --global http.sslVerify false
git config --global init.defaultBranch main
echo    done

echo.
echo === 5/8 Initializing git repo ===
git init -b main 2>&1 | findstr /v "Initialized"
git add .
git -c user.email="se@local" -c user.name="Se" commit -m "Initial local state" 2>&1 | findstr /v "create mode"
echo    done

echo.
echo === 6/8 Linking to github.com/swzhukov/bit-technolog-prototype ===
git remote add origin https://github.com/swzhukov/bit-technolog-prototype.git
git fetch origin 2>&1 | findstr /v "^From"
echo    done

echo.
echo === 7/8 Syncing with remote (will overwrite your files with my latest) ===
git reset --hard origin/main 2>&1 | findstr /v "^HEAD"
echo    done

echo.
echo === 8/8 Restoring .env ===
if exist .env.bak (
    move /Y .env.bak .env >nul
    echo    .env restored
) else (
    echo    no .env.bak - check if you have .env
)

echo.
echo ===========================================
echo  DONE!
echo.
echo  Test it:
echo    git pull
echo.
echo  Then start server:
echo    python app.py
echo ===========================================
echo.
pause
