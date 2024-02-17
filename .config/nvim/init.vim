" ========= Improved Functionality =========

" Enable syntax highlighting 
syntax on

" Display line numbers
set number

" Display relative line numbers (numbers adjusted based on cursor position)
set relativenumber 

" Make searches case-insensitive by default
set ignorecase

" ...Unless explicitly using capital letters
set smartcase

" Enable persistent undo (save undo history across sessions)
set undofile

" Enable file backups
set backup

" Ensure directories exist beforehand (optional, but good practice)
if empty(glob("~/.cache/nvim"))
    call mkdir("~/.cache/nvim", "p")
endif

" Set backupdir
set backupdir=~/.cache/nvim/backup/

" Set directory (for swap files)
set directory=~/.cache/nvim/swap// 

" Show visual indication of search matches as you type
set incsearch

" Show the matching bracket/parenthesis when cursor is over one
set showmatch

" ========= Indentation and Tabs =========

" Set tab width to 4 spaces
set tabstop=4

" Set indentation level to 4 spaces
set shiftwidth=4

" Convert tabs to spaces when inserted
set expandtab

" ========= User Interface =========

" Enable the mouse in all modes (may not work in all terminals)
set mouse=a

" Show the location of the cursor with line and column numbers
set ruler

" Cursor highlighting
set cursorline
hi CursorLine ctermbg=238
set cursorcolumn
hi CursorColumn ctermbg=238

" Disable cursor highlighting on entering Visual modes
autocmd ModeChanged *:[vV\x16] set nocursorline nocursorcolumn

" Enable cursor highlighting on leaving Visual modes
autocmd ModeChanged [vV\x16]:* set cursorline cursorcolumn

" Jump to last position when reopening a file
autocmd BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") | exe "normal! g'\"" | exe "normal! zz" | endif

" ========= Custom commands =========

" Clear search highlighting on ESC
nnoremap <esc> <esc>:noh<CR>

" Copy selected text to the system clipboard in visual mode
vnoremap <Leader>y "+y
" Paste the system clipboard in normal mode
nnoremap <Leader>p "+p

