# Getting AI Feedback on Your Report

This repository includes an automated system that provides AI-powered feedback on your student reports. Follow these simple steps to request feedback.

## Quick Start

### Prerequisites
- Your changes must be committed to git
- Your commits must be pushed to GitHub
- You need to be in the root directory of this repository

### How to Request Feedback

Simply run the feedback script from your terminal:

```bash
./get-feedback.sh
```

That's it! The script will:
1. ✅ Check that all your changes are committed
2. ✅ Verify that all commits are pushed to GitHub
3. 📝 Create a new version tag (v0.0.1, v0.0.2, etc.)
4. 🚀 Push the tag to GitHub (this triggers the feedback workflow)

### What Happens Next

Once the script completes successfully:
- The feedback workflow will start running on GitHub
- You'll see a link to the Actions page where you can monitor progress
- Within a few minutes, the AI will analyze your report and provide feedback
- The feedback will be posted as a comment on your commit

## Troubleshooting

### Error: "Not in a git repository"
- You need to run the script from the root directory of the repository
- Make sure you're in the folder that contains the `.git` directory

### Error: "You have uncommitted changes"
You have changes that haven't been committed yet. Commit them first:

```bash
git add .
git commit -m "Your commit message here"
```

Then run `./get-feedback.sh` again.

### Error: "You have untracked files"
You have new files that haven't been added to git. Either:

Add and commit them:
```bash
git add .
git commit -m "Add new files"
```

Or add them to `.gitignore` if they shouldn't be tracked:
```bash
echo "filename" >> .gitignore
git add .gitignore
git commit -m "Update gitignore"
```

### Error: "You have unpushed commits"
Your commits exist locally but haven't been pushed to GitHub yet. Push them:

```bash
git push
```

Then run `./get-feedback.sh` again.

## What Gets Analyzed

The feedback workflow analyzes:
- Your written explanations and descriptions
- Code implementation and documentation
- Results and visualizations
- Report structure and clarity
- Alignment with assignment rubric

## Tips for Better Feedback

1. **Make your latest commit before running the script** - The feedback is based on whatever the current HEAD of your main branch is
2. **Push all your work** - Make sure everything is committed and pushed before requesting feedback
3. **Review previous feedback** - Check the Actions tab to see feedback from previous requests
4. **Request feedback multiple times** - You can run the script multiple times to get feedback as you improve your work

## Understanding the Version Tags

Each time you run `./get-feedback.sh`, it creates a new version tag:
- First feedback: v0.0.1
- Second feedback: v0.0.2
- And so on...

These tags help track which version of your work was analyzed for each feedback request.

## Need Help?

If you encounter issues:
1. Check that you're in the repository root directory
2. Make sure all changes are committed: `git status`
3. Make sure all commits are pushed: `git push`
4. Review the error message from the script

If the script succeeds but you don't see feedback:
- Check the Actions tab on GitHub
- Look for the workflow that matches your tag (e.g., "v0.0.1")
- Wait a few minutes - it may still be processing
