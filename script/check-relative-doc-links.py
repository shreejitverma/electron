#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import re


SOURCE_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DOCS_DIR = os.path.join(SOURCE_ROOT, 'docs')


def main():
  os.chdir(SOURCE_ROOT)

  filepaths = []
  totalDirs = 0
  try:
    for root, dirs, files in os.walk(DOCS_DIR):
      totalDirs += len(dirs)
      filepaths.extend(os.path.join(root, f) for f in files if f.endswith('.md'))
  except KeyboardInterrupt:
    print('Keyboard interruption. Please try again.')
    return

  totalBrokenLinks = sum(getBrokenLinks(path) for path in filepaths)
  print(((f'Parsed through {len(filepaths)}' +
          ' files within docs directory and its ') + str(totalDirs) +
         ' subdirectories.'))
  print(f'Found {str(totalBrokenLinks)} broken relative links.')
  return totalBrokenLinks


def getBrokenLinks(filepath):
  currentDir = os.path.dirname(filepath)
  brokenLinks = []

  try:
    f = open(filepath, 'r')
    lines = f.readlines()
  except KeyboardInterrupt:
    print('Keyboard interruption while parsing. Please try again.')
  finally:
    f.close()

  linkRegexLink = re.compile('\[(.*?)\]\((?P<link>(.*?))\)')
  referenceLinkRegex = re.compile(
      '^\s{0,3}\[.*?\]:\s*(?P<link>[^<\s]+|<[^<>\r\n]+>)'
  )
  links = []
  for line in lines:
    matchLinks = linkRegexLink.search(line)
    matchReferenceLinks = referenceLinkRegex.search(line)
    if matchLinks:
      relativeLink = matchLinks['link']
      if not str(relativeLink).startswith('http'):
        links.append(relativeLink)
    if matchReferenceLinks:
      referenceLink = matchReferenceLinks['link'].strip('<>')
      if not str(referenceLink).startswith('http'):
        links.append(referenceLink)

  for link in links:
    sections = link.split('#')
    if len(sections) < 2:
      if not os.path.isfile(os.path.join(currentDir, link)):
        brokenLinks.append(link)
    elif str(link).startswith('#'):
      if not checkSections(sections, lines):
        brokenLinks.append(link)
    else:
      tempFile = os.path.join(currentDir, sections[0])
      if os.path.isfile(tempFile):
        try:
          newFile = open(tempFile, 'r')
          newLines = newFile.readlines()
        except KeyboardInterrupt:
          print('Keyboard interruption while parsing. Please try again.')
        finally:
          newFile.close()

        if not checkSections(sections, newLines):
          brokenLinks.append(link)
      else:
        brokenLinks.append(link)


  print_errors(filepath, brokenLinks)
  return len(brokenLinks)


def checkSections(sections, lines):
  invalidCharsRegex = '[^A-Za-z0-9_ \-]'
  sectionHeader = sections[1]
  regexSectionTitle = re.compile('# (?P<header>.*)')
  for line in lines:
    if matchHeader := regexSectionTitle.search(line):
      # This does the following to slugify a header name:
      #  * Replace whitespace with dashes
      #  * Strip anything that's not alphanumeric or a dash
      #  * Anything quoted with backticks (`) is an exception and will
      #    not have underscores stripped
      matchHeader = str(matchHeader['header']).replace(' ', '-')
      matchHeader = ''.join(
          map(
              lambda match: (re.sub(invalidCharsRegex, '', match[0]) + re.sub(
                  f'{invalidCharsRegex}|_', '', match[1])),
              re.findall('(`[^`]+`)|([^`]+)', matchHeader),
          ))
      if matchHeader.lower() == sectionHeader:
        return True
  return False


def print_errors(filepath, brokenLink):
  if brokenLink:
    print(f"File Location: {filepath}")
    for link in brokenLink:
      print("\tBroken links: " + link)


if __name__ == '__main__':
  sys.exit(main())
