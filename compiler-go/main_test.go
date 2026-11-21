package main

import "testing"

func TestBanner(t *testing.T) {
	if got := banner(); got != "suiyu-go-phase0" {
		t.Fatalf("banner() = %q", got)
	}
}
