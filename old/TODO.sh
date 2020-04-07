#!/bin/bash
clear
grep '#TODO' quest.py | sed 's/^.*#//'
